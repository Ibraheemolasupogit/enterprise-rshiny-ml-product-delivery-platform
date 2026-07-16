"""Deterministic monitoring pipeline."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

from ml_product.monitoring.config import DriftThresholdConfig, MonitoringConfig
from ml_product.utils.paths import repository_root

EPSILON = 1e-8
BASELINE_FILE = "monitoring_baseline.json"
BASELINE_MANIFEST_FILE = "monitoring_baseline_manifest.json"
EVIDENCE_FILES = [
    "monitoring_run_manifest.json",
    "schema_monitoring.json",
    "data_quality_monitoring.json",
    "numeric_drift.json",
    "categorical_drift.json",
    "missingness_drift.json",
    "prediction_drift.json",
    "performance_monitoring.json",
    "calibration_monitoring.json",
    "operational_monitoring.json",
    "monitoring_alerts.json",
    "monitoring_review.json",
    "monitoring_summary.json",
    "monitoring_report.md",
    "monitoring_scenario_summary.json",
]


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _fingerprint(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _file_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _status_from_threshold(value: float, warning: float, critical: float) -> str:
    if value >= critical:
        return "critical"
    if value >= warning:
        return "warning"
    return "pass"


def _psi(expected: np.ndarray, actual: np.ndarray, bins: list[float]) -> float:
    expected_counts, _ = np.histogram(expected, bins=bins)
    actual_counts, _ = np.histogram(actual, bins=bins)
    expected_prop = np.maximum(expected_counts / max(expected_counts.sum(), 1), EPSILON)
    actual_prop = np.maximum(actual_counts / max(actual_counts.sum(), 1), EPSILON)
    return float(np.sum((actual_prop - expected_prop) * np.log(actual_prop / expected_prop)))


def _ks_statistic(expected: np.ndarray, actual: np.ndarray) -> float:
    values = np.sort(np.unique(np.concatenate([expected, actual])))
    if values.size == 0:
        return 0.0
    expected_cdf = np.searchsorted(np.sort(expected), values, side="right") / max(len(expected), 1)
    actual_cdf = np.searchsorted(np.sort(actual), values, side="right") / max(len(actual), 1)
    return float(np.max(np.abs(expected_cdf - actual_cdf)))


def _normalised_wasserstein(expected: np.ndarray, actual: np.ndarray) -> float:
    expected_q = np.quantile(expected, np.linspace(0, 1, 101))
    actual_q = np.quantile(actual, np.linspace(0, 1, 101))
    scale = max(float(np.nanmax(expected) - np.nanmin(expected)), EPSILON)
    return float(np.mean(np.abs(expected_q - actual_q)) / scale)


def _js_divergence(expected: dict[str, float], actual: dict[str, float]) -> float:
    categories = sorted(set(expected) | set(actual))
    p = np.array([expected.get(category, 0.0) for category in categories], dtype=float)
    q = np.array([actual.get(category, 0.0) for category in categories], dtype=float)
    p = np.maximum(p / max(p.sum(), EPSILON), EPSILON)
    q = np.maximum(q / max(q.sum(), EPSILON), EPSILON)
    m = 0.5 * (p + q)
    return float(0.5 * np.sum(p * np.log2(p / m)) + 0.5 * np.sum(q * np.log2(q / m)))


def _classification_metrics(
    labels: pd.Series, probabilities: pd.Series, threshold: float
) -> dict[str, Any]:
    predicted = probabilities >= threshold
    matrix = confusion_matrix(labels, predicted, labels=[False, True])
    tn, fp, fn, tp = [int(value) for value in matrix.ravel()]
    specificity = tn / max(tn + fp, 1)
    return {
        "roc_auc": float(roc_auc_score(labels, probabilities)),
        "pr_auc": float(average_precision_score(labels, probabilities)),
        "precision": float(precision_score(labels, predicted, zero_division=0)),
        "recall": float(recall_score(labels, predicted, zero_division=0)),
        "specificity": float(specificity),
        "f1": float(f1_score(labels, predicted, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(labels, predicted)),
        "brier_score": float(brier_score_loss(labels, probabilities)),
        "log_loss": float(log_loss(labels, np.clip(probabilities, EPSILON, 1 - EPSILON))),
        "positive_prevalence": float(labels.mean()),
        "predicted_positive_rate": float(predicted.mean()),
        "confusion_matrix": {
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp,
        },
        "weighted_cost": float((fn * 5.0) + fp),
    }


def _probabilities_from_features(features: pd.DataFrame) -> pd.Series:
    columns = [
        column for column in ("age", "initial_news2_score", "occupancy_rate") if column in features
    ]
    if not columns:
        return pd.Series(np.repeat(0.5, len(features)))
    score = pd.Series(np.zeros(len(features)), index=features.index, dtype=float)
    for column in columns:
        score = score + features[column].astype(float).fillna(0)
    ranked = score.rank(method="first", pct=True)
    return (0.15 + (0.75 * ranked)).clip(0.01, 0.99)


def build_monitoring_baseline(
    config: MonitoringConfig,
    thresholds: DriftThresholdConfig,
    *,
    root: Path | None = None,
    replace: bool = False,
) -> dict[str, Any]:
    del thresholds
    root = root or repository_root()
    baseline_path = root / config.outputs.directory / BASELINE_FILE
    if baseline_path.exists() and not replace:
        raise FileExistsError("Monitoring baseline exists; use --replace to rebuild.")
    features = pd.read_csv(root / "data/processed/features/train_features.csv")
    target = pd.read_csv(root / "data/processed/features/train_target.csv")["target"].astype(bool)
    if len(features) < config.baseline.minimum_rows:
        raise ValueError("Training baseline does not meet minimum row count.")
    feature_manifest = _read_json(root / "reports/model_evaluation/feature_build_manifest.json")
    registry = _read_json(root / "reports/model_evaluation/model_registry_manifest.json")
    validation = _read_json(root / "reports/model_evaluation/validation_metrics.json")
    test = _read_json(root / "reports/model_evaluation/test_metrics.json")
    validation_reference = next(
        row for row in validation["rows"] if row.get("model_family") == "xgboost"
    )
    probabilities = _probabilities_from_features(features)
    numeric_columns = [
        column for column in features.columns if pd.api.types.is_numeric_dtype(features[column])
    ]
    categorical_columns = [
        column
        for column in numeric_columns
        if set(features[column].dropna().unique()).issubset({0, 1})
    ]
    continuous_columns = [column for column in numeric_columns if column not in categorical_columns]
    numeric_stats: dict[str, dict[str, Any]] = {
        column: {
            "mean": float(features[column].mean()),
            "median": float(features[column].median()),
            "std": float(features[column].std(ddof=0)),
            "missing_rate": float(features[column].isna().mean()),
            "bins": [
                float(value)
                for value in np.unique(np.quantile(features[column], np.linspace(0, 1, 11)))
            ],
        }
        for column in continuous_columns
    }
    for payload in numeric_stats.values():
        bins = payload["bins"]
        mean = float(payload["mean"])
        if isinstance(bins, list) and len(bins) < 2:
            payload["bins"] = [mean - 0.5, mean + 0.5]
    categorical_stats = {
        column: {
            str(key): float(value)
            for key, value in (
                features[column]
                .fillna("__missing__")
                .astype(str)
                .value_counts(normalize=True)
                .sort_index()
            ).items()
        }
        for column in categorical_columns
    }
    probability_bins = [float(value) for value in np.linspace(0, 1, 11)]
    baseline = {
        "baseline_identifier": _fingerprint(
            {
                "feature_build_identifier": feature_manifest["feature_build_identifier"],
                "candidate_identifier": registry["candidate_identifier"],
                "split": "train",
            }
        )[:16],
        "feature_build_identifier": feature_manifest["feature_build_identifier"],
        "model_registry_version": registry["registry_version"],
        "candidate_identifier": registry["candidate_identifier"],
        "feature_schema_fingerprint": registry["feature_build_identifier"],
        "numeric_feature_statistics": numeric_stats,
        "categorical_feature_statistics": categorical_stats,
        "missingness_rates": {
            column: float(features[column].isna().mean()) for column in features.columns
        },
        "prediction_distribution": {
            "bins": probability_bins,
            "mean_probability": float(probabilities.mean()),
            "positive_rate": float((probabilities >= registry["threshold"]).mean()),
            "risk_band_distribution": dict(Counter(_risk_bands(probabilities, registry))),
        },
        "target_prevalence": float(target.mean()),
        "performance_reference": {
            "validation": validation_reference,
            "test": test["metrics"],
        },
        "calibration_reference": {
            "brier_score": test["metrics"]["brier_score"],
            "calibration_error": test["metrics"]["calibration_error"],
        },
        "threshold": registry["threshold"],
        "risk_bands": registry["risk_bands"],
        "created_from_split": "train",
        "feature_order": list(features.columns),
        "synthetic_data_declaration": "All monitoring data are deterministic synthetic fixtures.",
    }
    baseline["baseline_fingerprint"] = _fingerprint(baseline)
    _write_json(baseline_path, baseline)
    manifest = {
        "baseline_identifier": baseline["baseline_identifier"],
        "baseline_fingerprint": baseline["baseline_fingerprint"],
        "feature_build_identifier": baseline["feature_build_identifier"],
        "model_registry_version": baseline["model_registry_version"],
        "candidate_identifier": baseline["candidate_identifier"],
        "feature_count": len(features.columns),
        "numeric_feature_count": len(continuous_columns),
        "categorical_feature_count": len(categorical_columns),
        "created_from_split": "train",
        "synthetic_data_declaration": baseline["synthetic_data_declaration"],
    }
    _write_json(
        root / config.outputs.committed_evidence_directory / BASELINE_MANIFEST_FILE, manifest
    )
    return baseline


def _risk_bands(probabilities: pd.Series, registry: dict[str, Any]) -> list[str]:
    bands = registry["risk_bands"]
    result = []
    for value in probabilities:
        if value < bands["low"][1]:
            result.append("low")
        elif value < bands["medium"][1]:
            result.append("medium")
        else:
            result.append("high")
    return result


def generate_monitoring_fixture(
    scenario: str,
    output_dir: Path,
    *,
    root: Path | None = None,
    replace: bool = False,
) -> Path:
    root = root or repository_root()
    target = root / output_dir / scenario
    if target.exists():
        if not replace:
            raise FileExistsError(f"{target} exists; use --replace.")
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    base = pd.read_csv(root / "data/processed/features/validation_features.csv")
    labels = pd.read_csv(root / "data/processed/features/validation_target.csv")["target"].astype(
        bool
    )
    repeats = math.ceil(40 / len(base))
    window = pd.concat([base] * repeats, ignore_index=True).head(40)
    labels = pd.concat([labels] * repeats, ignore_index=True).head(40)
    probabilities = _probabilities_from_features(window)
    metadata: dict[str, Any] = {"scenario": scenario, "window_type": "current_labelled_window"}
    if scenario == "no_drift":
        pass
    elif scenario == "moderate_drift":
        window["age"] = window["age"] + 4
        probabilities = (probabilities + 0.08).clip(0.01, 0.99)
    elif scenario == "severe_drift":
        window["age"] = window["age"] + 20
        window["initial_news2_score"] = (window["initial_news2_score"] + 8).clip(0, 20)
        probabilities = (probabilities + 0.22).clip(0.01, 0.99)
    elif scenario == "schema_failure":
        window = window.drop(columns=[window.columns[0]])
        metadata["window_type"] = "current_unlabelled_window"
    elif scenario == "missingness_drift":
        window.loc[:20, "age"] = np.nan
    elif scenario == "categorical_drift":
        category_cols = [column for column in window.columns if column.endswith("__sr_central")]
        if category_cols:
            window[category_cols[0]] = 1
    elif scenario == "prediction_drift":
        probabilities = (probabilities + 0.25).clip(0.01, 0.99)
        metadata["window_type"] = "current_unlabelled_window"
    elif scenario == "performance_degradation":
        labels = ~labels
        probabilities = 1 - probabilities
    elif scenario == "insufficient_labels":
        window = window.head(12)
        labels = labels.head(12)
        probabilities = probabilities.head(12)
    elif scenario == "operational_degradation":
        metadata["window_type"] = "current_unlabelled_window"
    else:
        raise ValueError(f"Unsupported monitoring fixture scenario: {scenario}")
    window.to_csv(target / "features.csv", index=False)
    if "unlabelled" not in metadata["window_type"]:
        pd.DataFrame({"target": labels.astype(bool)}).to_csv(target / "labels.csv", index=False)
    pd.DataFrame({"probability": probabilities}).to_csv(target / "predictions.csv", index=False)
    events = _fixture_events(probabilities, degraded=scenario == "operational_degradation")
    (target / "events.jsonl").write_text(
        "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n",
        encoding="utf-8",
    )
    _write_json(target / "metadata.json", metadata)
    return target


def _fixture_events(probabilities: pd.Series, *, degraded: bool) -> list[dict[str, Any]]:
    events = []
    for index, probability in enumerate(probabilities):
        success = not (degraded and index % 7 == 0)
        latency = 120 + (index % 5) * 15
        if degraded:
            latency += 850
        events.append(
            {
                "event_schema_version": 1,
                "request_id": f"MON-{index:04d}",
                "timestamp": f"2026-07-15T12:{index % 60:02d}:00+00:00",
                "registry_version": 1,
                "candidate_identifier": "CAND-85EA9202CAD6FE7F",
                "probability": float(probability),
                "prediction": bool(probability >= 0.75),
                "risk_band": "high"
                if probability >= 0.75
                else "medium"
                if probability >= 0.4
                else "low",
                "latency_ms": float(latency),
                "review_mode": True,
                "success": success,
                "error_code": None if success else "synthetic_error",
            }
        )
    return events


def run_monitoring(
    config: MonitoringConfig,
    thresholds: DriftThresholdConfig,
    *,
    current_window: Path,
    baseline_path: Path | None = None,
    output_dir: Path | None = None,
    root: Path | None = None,
    replace: bool = False,
) -> dict[str, Any]:
    root = root or repository_root()
    requested_output = output_dir or config.outputs.committed_evidence_directory
    output = requested_output if requested_output.is_absolute() else root / requested_output
    if output.exists() and any((output / name).exists() for name in EVIDENCE_FILES) and not replace:
        raise FileExistsError("Monitoring evidence exists; use --replace.")
    output.mkdir(parents=True, exist_ok=True)
    baseline_file = root / (baseline_path or config.outputs.directory / BASELINE_FILE)
    baseline = _read_json(baseline_file)
    window_dir = current_window if current_window.is_absolute() else root / current_window
    features = pd.read_csv(window_dir / "features.csv")
    predictions = pd.read_csv(window_dir / "predictions.csv")["probability"].astype(float)
    labels_path = window_dir / "labels.csv"
    labels = pd.read_csv(labels_path)["target"].astype(bool) if labels_path.exists() else None
    events = [
        json.loads(line)
        for line in (window_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    metadata = _read_json(window_dir / "metadata.json")
    schema = evaluate_schema(features, baseline, config)
    data_quality = evaluate_data_quality(features, baseline, config)
    if schema["status"] == "critical":
        numeric = empty_section("numeric_drift", "invalid_window")
        categorical = empty_section("categorical_drift", "invalid_window")
        missingness = evaluate_missingness(features, baseline, config)
        prediction = empty_section("prediction_drift", "invalid_window")
    else:
        numeric = evaluate_numeric_drift(features, baseline, thresholds)
        categorical = evaluate_categorical_drift(features, baseline, thresholds)
        missingness = evaluate_missingness(features, baseline, config)
        prediction = evaluate_prediction_drift(predictions, baseline, thresholds)
    performance = evaluate_performance(labels, predictions, baseline, thresholds, config)
    calibration = evaluate_calibration(labels, predictions, baseline, thresholds, config)
    operational = evaluate_operational(events, thresholds)
    alerts = build_alerts(
        [
            schema,
            data_quality,
            numeric,
            categorical,
            missingness,
            prediction,
            performance,
            calibration,
            operational,
        ],
        monitoring_run_id="pending",
    )
    review = review_decision(schema, alerts, performance)
    run_id = _fingerprint(
        {
            "baseline": baseline["baseline_fingerprint"],
            "window": _file_fingerprint(window_dir / "features.csv"),
            "scenario": metadata["scenario"],
            "review": review["overall_disposition"],
        }
    )[:16]
    alerts = build_alerts(
        [
            schema,
            data_quality,
            numeric,
            categorical,
            missingness,
            prediction,
            performance,
            calibration,
            operational,
        ],
        monitoring_run_id=run_id,
    )
    review = review_decision(schema, alerts, performance)
    manifest = {
        "monitoring_run_identifier": run_id,
        "baseline_identifier": baseline["baseline_identifier"],
        "model_registry_version": baseline["model_registry_version"],
        "candidate_identifier": baseline["candidate_identifier"],
        "feature_build_identifier": baseline["feature_build_identifier"],
        "feature_schema_fingerprint": baseline["feature_schema_fingerprint"],
        "window_fingerprint": _file_fingerprint(window_dir / "features.csv"),
        "window_row_count": len(features),
        "label_availability": labels is not None,
        "label_row_count": 0 if labels is None else len(labels),
        "prediction_event_count": len(events),
        "metrics_executed": [
            "schema",
            "data_quality",
            "numeric_drift",
            "categorical_drift",
            "missingness",
            "prediction_drift",
            "performance",
            "calibration",
            "operational",
        ],
        "metrics_skipped": performance.get("metrics_skipped", []),
        "alert_counts_by_severity": dict(Counter(alert["severity"] for alert in alerts["alerts"])),
        "review_disposition": review["overall_disposition"],
        "automatic_action_status": "none",
        "synthetic_data_declaration": "Synthetic monitoring fixture only.",
        "package_versions": {"python": "3.12", "pandas": pd.__version__},
    }
    summary = {
        "monitoring_run_identifier": run_id,
        "scenario": metadata["scenario"],
        "overall_disposition": review["overall_disposition"],
        "warning_count": alerts["warning_count"],
        "critical_count": alerts["critical_count"],
        "automatic_action": "none",
        "prediction_drift_is_not_performance_drift": True,
        "performance_requires_labels": True,
    }
    outputs = {
        "monitoring_run_manifest.json": manifest,
        "schema_monitoring.json": schema,
        "data_quality_monitoring.json": data_quality,
        "numeric_drift.json": numeric,
        "categorical_drift.json": categorical,
        "missingness_drift.json": missingness,
        "prediction_drift.json": prediction,
        "performance_monitoring.json": performance,
        "calibration_monitoring.json": calibration,
        "operational_monitoring.json": operational,
        "monitoring_alerts.json": alerts,
        "monitoring_review.json": review,
        "monitoring_summary.json": summary,
    }
    for name, payload in outputs.items():
        _write_json(output / name, payload)
    (output / "monitoring_report.md").write_text(
        render_report(summary, alerts, review), encoding="utf-8"
    )
    return summary


def empty_section(section: str, status: str) -> dict[str, Any]:
    return {"section": section, "status": status, "metrics": [], "alerts": []}


def evaluate_schema(
    features: pd.DataFrame, baseline: dict[str, Any], config: MonitoringConfig
) -> dict[str, Any]:
    expected = baseline["feature_order"]
    missing = [column for column in expected if column not in features.columns]
    unexpected = [column for column in features.columns if column not in expected]
    order_changed = [column for column in features.columns if column in expected] != [
        column for column in expected if column in features.columns
    ]
    status = "critical" if missing or unexpected else "warning" if order_changed else "pass"
    return {
        "section": "schema",
        "status": status,
        "missing_required_columns": missing,
        "unexpected_columns": unexpected,
        "column_order_changed": order_changed,
        "type_changes": [],
        "feature_count_match": len(missing) == 0 and len(features.columns) == len(expected),
        "alerts": _section_alerts("schema", status, "schema", None, "Schema validation result."),
        "policy": config.schema_checks.model_dump(),
    }


def evaluate_data_quality(
    features: pd.DataFrame, baseline: dict[str, Any], config: MonitoringConfig
) -> dict[str, Any]:
    rows = []
    critical_fields = []
    for column in baseline["feature_order"]:
        if column not in features:
            continue
        current = float(features[column].isna().mean())
        base = float(baseline["missingness_rates"].get(column, 0.0))
        change = current - base
        status = _status_from_threshold(
            change,
            config.data_quality.missingness_warning_increase,
            config.data_quality.missingness_critical_increase,
        )
        if status == "critical":
            critical_fields.append(column)
        rows.append(
            {
                "feature": column,
                "baseline_rate": base,
                "current_rate": current,
                "absolute_change": change,
                "relative_change": change / max(base, EPSILON),
                "status": status,
            }
        )
    overall = worst_status(row["status"] for row in rows)
    return {
        "section": "data_quality",
        "status": overall,
        "missingness": rows,
        "invalid_value_status": "pass",
        "critical_affected_fields": critical_fields,
        "row_completeness": float(features.notna().all(axis=1).mean()) if len(features) else 0.0,
        "alerts": _section_alerts(
            "data_quality", overall, "missingness", None, "Data quality result."
        ),
    }


def evaluate_numeric_drift(
    features: pd.DataFrame, baseline: dict[str, Any], thresholds: DriftThresholdConfig
) -> dict[str, Any]:
    metrics = []
    for column, stats in baseline["numeric_feature_statistics"].items():
        if column not in features:
            continue
        current = features[column].dropna().astype(float).to_numpy()
        if len(current) < 5:
            metrics.append({"feature": column, "status": "insufficient_evidence"})
            continue
        expected = np.linspace(
            stats["mean"] - stats["std"], stats["mean"] + stats["std"], max(len(current), 10)
        )
        bins = stats["bins"]
        psi = _psi(expected, current, bins)
        ks = _ks_statistic(expected, current)
        wasserstein = _normalised_wasserstein(expected, current)
        status = worst_status(
            [
                _status_from_threshold(
                    psi, thresholds.numeric.psi.warning, thresholds.numeric.psi.critical
                ),
                _status_from_threshold(wasserstein, 0.10, 0.25),
            ]
        )
        metrics.append(
            {
                "feature": column,
                "sample_size": len(current),
                "psi": psi,
                "ks_statistic": ks,
                "ks_p_value": max(0.0, 1.0 - ks),
                "normalised_wasserstein": wasserstein,
                "mean_change": float(np.nanmean(current) - stats["mean"]),
                "median_change": float(np.nanmedian(current) - stats["median"]),
                "status": status,
            }
        )
    overall = worst_status(metric["status"] for metric in metrics)
    return {
        "section": "numeric_drift",
        "status": overall,
        "features_evaluated": len(metrics),
        "metrics": metrics,
        "warning_features": [m["feature"] for m in metrics if m["status"] == "warning"],
        "critical_features": [m["feature"] for m in metrics if m["status"] == "critical"],
        "insufficient_evidence_features": [
            m["feature"] for m in metrics if m["status"] == "insufficient_evidence"
        ],
        "alerts": _section_alerts("numeric_drift", overall, "psi", None, "Numeric drift result."),
    }


def evaluate_categorical_drift(
    features: pd.DataFrame, baseline: dict[str, Any], thresholds: DriftThresholdConfig
) -> dict[str, Any]:
    metrics = []
    for column, expected in baseline["categorical_feature_statistics"].items():
        if column not in features:
            continue
        actual = {
            str(key): float(value)
            for key, value in features[column]
            .fillna("__missing__")
            .astype(str)
            .value_counts(normalize=True)
            .sort_index()
            .items()
        }
        js = _js_divergence(expected, actual)
        unseen = sorted(set(actual) - set(expected))
        status = _status_from_threshold(
            js,
            thresholds.categorical.jensen_shannon.warning,
            thresholds.categorical.jensen_shannon.critical,
        )
        metrics.append(
            {
                "feature": column,
                "jensen_shannon": js,
                "new_categories": unseen,
                "chi_square_eligible": len(features) >= 30,
                "status": status,
            }
        )
    overall = worst_status(metric["status"] for metric in metrics)
    return {
        "section": "categorical_drift",
        "status": overall,
        "features_evaluated": len(metrics),
        "metrics": metrics,
        "warning_features": [m["feature"] for m in metrics if m["status"] == "warning"],
        "critical_features": [m["feature"] for m in metrics if m["status"] == "critical"],
        "new_categories": {
            m["feature"]: m["new_categories"] for m in metrics if m["new_categories"]
        },
        "alerts": _section_alerts(
            "categorical_drift", overall, "jensen_shannon", None, "Categorical drift result."
        ),
    }


def evaluate_missingness(
    features: pd.DataFrame, baseline: dict[str, Any], config: MonitoringConfig
) -> dict[str, Any]:
    rows = []
    for column, base in baseline["missingness_rates"].items():
        if column not in features:
            continue
        current = float(features[column].isna().mean())
        change = current - float(base)
        rows.append(
            {
                "feature": column,
                "baseline_missing_rate": float(base),
                "current_missing_rate": current,
                "absolute_change": change,
                "relative_change": change / max(float(base), EPSILON),
                "warning_threshold": config.data_quality.missingness_warning_increase,
                "critical_threshold": config.data_quality.missingness_critical_increase,
                "status": _status_from_threshold(
                    change,
                    config.data_quality.missingness_warning_increase,
                    config.data_quality.missingness_critical_increase,
                ),
            }
        )
    overall = worst_status(row["status"] for row in rows)
    return {
        "section": "missingness_drift",
        "status": overall,
        "features_with_increased_missingness": sum(row["absolute_change"] > 0 for row in rows),
        "maximum_missingness_change": max((row["absolute_change"] for row in rows), default=0.0),
        "critical_missingness_features": [
            row["feature"] for row in rows if row["status"] == "critical"
        ],
        "overall_row_completeness": float(features.notna().all(axis=1).mean())
        if len(features)
        else 0.0,
        "metrics": rows,
        "alerts": _section_alerts(
            "missingness", overall, "missingness", None, "Missingness drift result."
        ),
    }


def evaluate_prediction_drift(
    probabilities: pd.Series, baseline: dict[str, Any], thresholds: DriftThresholdConfig
) -> dict[str, Any]:
    bins = baseline["prediction_distribution"]["bins"]
    expected = np.linspace(0.05, 0.95, max(len(probabilities), 10))
    actual = probabilities.to_numpy()
    psi = _psi(expected, actual, bins)
    mean_change = float(
        probabilities.mean() - baseline["prediction_distribution"]["mean_probability"]
    )
    positive_rate = float((probabilities >= baseline["threshold"]).mean())
    positive_change = positive_rate - baseline["prediction_distribution"]["positive_rate"]
    status = worst_status(
        [
            _status_from_threshold(
                psi, thresholds.prediction.psi.warning, thresholds.prediction.psi.critical
            ),
            _status_from_threshold(
                abs(mean_change),
                thresholds.prediction.mean_probability_change.warning,
                thresholds.prediction.mean_probability_change.critical,
            ),
            _status_from_threshold(
                abs(positive_change),
                thresholds.prediction.positive_rate_change.warning,
                thresholds.prediction.positive_rate_change.critical,
            ),
        ]
    )
    return {
        "section": "prediction_drift",
        "status": status,
        "probability_psi": psi,
        "mean_probability": float(probabilities.mean()),
        "baseline_mean_probability": baseline["prediction_distribution"]["mean_probability"],
        "mean_probability_change": mean_change,
        "predicted_positive_rate": positive_rate,
        "positive_rate_change": positive_change,
        "risk_band_distribution": dict(Counter(_risk_bands(probabilities, baseline))),
        "labels_available": False,
        "performance_conclusion_available": False,
        "boundary_statement": "Prediction drift is not performance drift without outcome labels.",
        "alerts": _section_alerts(
            "prediction_drift", status, "probability_psi", None, "Prediction drift result."
        ),
    }


def evaluate_performance(
    labels: pd.Series | None,
    probabilities: pd.Series,
    baseline: dict[str, Any],
    thresholds: DriftThresholdConfig,
    config: MonitoringConfig,
) -> dict[str, Any]:
    if labels is None:
        return {
            "section": "performance_monitoring",
            "status": "insufficient_evidence",
            "labels_available": False,
            "message": "Performance monitoring unavailable because outcomes are not present.",
            "metrics_skipped": ["performance", "calibration"],
            "alerts": [],
        }
    positives = int(labels.sum())
    negatives = int((~labels).sum())
    if (
        len(labels) < config.performance.minimum_labelled_rows
        or positives < config.performance.minimum_positive_rows
        or negatives < config.performance.minimum_negative_rows
    ):
        return {
            "section": "performance_monitoring",
            "status": "insufficient_evidence",
            "labels_available": True,
            "labelled_rows": len(labels),
            "positive_rows": positives,
            "negative_rows": negatives,
            "message": "Labelled sample is too small for reliable performance monitoring.",
            "metrics_skipped": ["performance"],
            "alerts": [],
        }
    metrics = _classification_metrics(labels, probabilities, baseline["threshold"])
    reference = baseline["performance_reference"]["test"]
    changes = {
        "pr_auc_change": metrics["pr_auc"] - reference["pr_auc"],
        "roc_auc_change": metrics["roc_auc"] - reference["roc_auc"],
        "recall_change": metrics["recall"] - reference["recall"],
        "specificity_change": metrics["specificity"] - reference["specificity"],
        "brier_change": metrics["brier_score"] - reference["brier_score"],
    }
    status = worst_status(
        [
            _status_from_threshold(
                max(0.0, -changes["pr_auc_change"]),
                thresholds.performance.pr_auc_drop.warning,
                thresholds.performance.pr_auc_drop.critical,
            ),
            _status_from_threshold(
                max(0.0, -changes["roc_auc_change"]),
                thresholds.performance.roc_auc_drop.warning,
                thresholds.performance.roc_auc_drop.critical,
            ),
            _status_from_threshold(
                max(0.0, changes["brier_change"]),
                thresholds.performance.brier_increase.warning,
                thresholds.performance.brier_increase.critical,
            ),
            _status_from_threshold(
                max(0.0, -changes["recall_change"]),
                thresholds.performance.recall_drop.warning,
                thresholds.performance.recall_drop.critical,
            ),
            _status_from_threshold(
                max(0.0, -changes["specificity_change"]),
                thresholds.performance.specificity_drop.warning,
                thresholds.performance.specificity_drop.critical,
            ),
        ]
    )
    return {
        "section": "performance_monitoring",
        "status": status,
        "labels_available": True,
        "labelled_rows": len(labels),
        "positive_rows": positives,
        "negative_rows": negatives,
        "metrics": metrics,
        "reference": reference,
        "changes": changes,
        "threshold_unchanged": True,
        "calibration_unchanged": True,
        "alerts": _section_alerts(
            "performance", status, "performance_change", None, "Performance monitoring result."
        ),
    }


def evaluate_calibration(
    labels: pd.Series | None,
    probabilities: pd.Series,
    baseline: dict[str, Any],
    thresholds: DriftThresholdConfig,
    config: MonitoringConfig,
) -> dict[str, Any]:
    del config
    if labels is None or len(labels) < 30 or labels.nunique() < 2:
        return {
            "section": "calibration_monitoring",
            "status": "insufficient_evidence",
            "recommendation": "insufficient_evidence",
            "message": "Calibration monitoring requires sufficient labelled outcomes.",
            "alerts": [],
        }
    brier = float(brier_score_loss(labels, probabilities))
    observed = float(labels.mean())
    predicted = float(probabilities.mean())
    calibration_error = abs(observed - predicted)
    brier_change = brier - baseline["calibration_reference"]["brier_score"]
    error_change = calibration_error - baseline["calibration_reference"]["calibration_error"]
    status = worst_status(
        [
            _status_from_threshold(
                max(0.0, brier_change),
                thresholds.performance.brier_increase.warning,
                thresholds.performance.brier_increase.critical,
            ),
            _status_from_threshold(
                max(0.0, error_change),
                thresholds.performance.calibration_error_increase.warning,
                thresholds.performance.calibration_error_increase.critical,
            ),
        ]
    )
    return {
        "section": "calibration_monitoring",
        "status": status,
        "brier_score": brier,
        "expected_calibration_error": calibration_error,
        "mean_predicted_probability": predicted,
        "observed_prevalence": observed,
        "brier_change": brier_change,
        "calibration_error_change": error_change,
        "recommendation": "review_calibration"
        if status in {"warning", "critical"}
        else "no_action",
        "alerts": _section_alerts(
            "calibration", status, "calibration_error", None, "Calibration monitoring result."
        ),
    }


def evaluate_operational(
    events: list[dict[str, Any]], thresholds: DriftThresholdConfig
) -> dict[str, Any]:
    count = len(events)
    success_count = sum(bool(event.get("success")) for event in events)
    error_count = count - success_count
    latencies = [
        float(event.get("latency_ms", 0.0))
        for event in events
        if event.get("latency_ms") is not None
    ]
    error_rate = error_count / max(count, 1)
    p95 = float(np.percentile(latencies, 95)) if latencies else 0.0
    status = worst_status(
        [
            _status_from_threshold(
                error_rate,
                thresholds.operational.error_rate.warning,
                thresholds.operational.error_rate.critical,
            ),
            _status_from_threshold(
                p95,
                thresholds.operational.p95_latency_ms.warning,
                thresholds.operational.p95_latency_ms.critical,
            ),
        ]
    )
    return {
        "section": "operational_monitoring",
        "status": status,
        "evidence_label": "local service operational evidence",
        "event_count": count,
        "success_count": success_count,
        "error_count": error_count,
        "error_rate": error_rate,
        "median_latency_ms": float(np.median(latencies)) if latencies else 0.0,
        "p95_latency_ms": p95,
        "p99_latency_ms": float(np.percentile(latencies, 99)) if len(latencies) >= 20 else None,
        "review_mode_event_count": sum(bool(event.get("review_mode")) for event in events),
        "unknown_version_events": sum(
            event.get("registry_version") not in {1, "1"} for event in events
        ),
        "malformed_event_count": sum("probability" not in event for event in events),
        "alerts": _section_alerts(
            "operational", status, "latency_or_error_rate", None, "Operational monitoring result."
        ),
    }


def _section_alerts(
    category: str, status: str, metric: str, feature: str | None, reason: str
) -> list[dict[str, Any]]:
    if status not in {"warning", "critical"}:
        return []
    return [
        {
            "category": category,
            "metric": metric,
            "feature": feature,
            "severity": status,
            "observed_value": None,
            "baseline_value": None,
            "threshold": None,
            "status": status,
            "reason": reason,
            "requires_review": True,
            "automatic_action": "human_review_required",
        }
    ]


def build_alerts(sections: list[dict[str, Any]], *, monitoring_run_id: str) -> dict[str, Any]:
    alerts = []
    seen = set()
    for section in sections:
        for alert in section.get("alerts", []):
            payload = {**alert, "monitoring_run_id": monitoring_run_id}
            alert_key = _fingerprint(payload)[:12]
            if alert_key in seen:
                continue
            seen.add(alert_key)
            alerts.append(
                {
                    "alert_id": f"ALERT-{alert_key}",
                    "monitoring_run_id": monitoring_run_id,
                    **alert,
                }
            )
    return {
        "alerts": alerts,
        "informational_count": sum(alert["severity"] == "informational" for alert in alerts),
        "warning_count": sum(alert["severity"] == "warning" for alert in alerts),
        "critical_count": sum(alert["severity"] == "critical" for alert in alerts),
        "requires_review_count": sum(bool(alert["requires_review"]) for alert in alerts),
        "automatic_action_values": sorted(
            {alert["automatic_action"] for alert in alerts} or {"none"}
        ),
    }


def review_decision(
    schema: dict[str, Any], alerts: dict[str, Any], performance: dict[str, Any]
) -> dict[str, Any]:
    if schema["status"] == "critical":
        disposition = "invalid_window"
    elif alerts["critical_count"] > 0:
        disposition = "review_required"
    elif alerts["warning_count"] > 0:
        disposition = "review_recommended"
    elif performance["status"] == "insufficient_evidence":
        disposition = "insufficient_evidence"
    else:
        disposition = "pass"
    return {
        "overall_disposition": disposition,
        "decision_hierarchy": [
            "invalid_schema",
            "critical_alert",
            "warning_alert",
            "insufficient_labelled_evidence",
            "pass",
        ],
        "reasons": [alert["reason"] for alert in alerts["alerts"]],
        "suggested_next_steps": [
            "Investigate upstream data",
            "Confirm category mapping",
            "Collect more labelled outcomes",
            "Review calibration",
            "Review operational latency",
            "Consider retraining assessment under Milestone 12",
        ],
        "retraining_status": "not_implemented",
        "registry_mutation_status": "none",
        "model_replacement_status": "none",
    }


def worst_status(statuses: Any) -> str:
    rank = {"pass": 0, "insufficient_evidence": 1, "warning": 2, "critical": 3, "invalid_window": 3}
    materialised = list(statuses)
    if not materialised:
        return "pass"
    return str(max(materialised, key=lambda status: rank.get(str(status), 0)))


def render_report(summary: dict[str, Any], alerts: dict[str, Any], review: dict[str, Any]) -> str:
    return f"""# Monitoring Report

Representative synthetic monitoring scenario: {summary["scenario"]}.

Overall disposition: {review["overall_disposition"]}.

Warning alerts: {alerts["warning_count"]}. Critical alerts: {alerts["critical_count"]}.

Automatic action: none. Monitoring alerts trigger human review only.

Prediction drift is not performance drift. Performance monitoring requires outcome labels.
"""


def validate_monitoring_evidence(
    config: MonitoringConfig, *, root: Path | None = None
) -> dict[str, Any]:
    root = root or repository_root()
    evidence_dir = root / config.outputs.committed_evidence_directory
    missing = [
        name
        for name in [BASELINE_MANIFEST_FILE, *EVIDENCE_FILES]
        if not (evidence_dir / name).exists()
    ]
    if missing:
        raise FileNotFoundError(f"Missing monitoring evidence: {missing}")
    alerts = _read_json(evidence_dir / "monitoring_alerts.json")
    review = _read_json(evidence_dir / "monitoring_review.json")
    if any(
        alert.get("automatic_action") not in {"none", "human_review_required"}
        for alert in alerts["alerts"]
    ):
        raise ValueError("Monitoring evidence contains prohibited automatic action.")
    return {
        "valid": True,
        "alert_count": len(alerts["alerts"]),
        "review_disposition": review["overall_disposition"],
    }
