"""Milestone 6 deterministic model training workflow."""

from __future__ import annotations

import platform
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn

from ml_product.modelling.baselines import fit_majority_baseline, fit_prevalence_baseline
from ml_product.modelling.calibration import Calibrator, select_calibration
from ml_product.modelling.comparison import comparison_payload
from ml_product.modelling.config import ModelTrainingConfig, ThresholdConfig
from ml_product.modelling.data import ModelData, load_model_data
from ml_product.modelling.evaluation import evaluate_predictions
from ml_product.modelling.explainability import build_explainability, build_global_explainability
from ml_product.modelling.fairness import build_fairness_report
from ml_product.modelling.logistic_regression import train_logistic_regression
from ml_product.modelling.metadata import (
    config_fingerprint,
    semantic_model_identifier,
    timestamp_utc,
)
from ml_product.modelling.prediction import predict_probability
from ml_product.modelling.random_forest import train_random_forest
from ml_product.modelling.reporting import evaluation_report, model_card
from ml_product.modelling.selection import recommend_candidate
from ml_product.modelling.thresholding import analyse_thresholds
from ml_product.modelling.writers import prepare_directory, write_joblib, write_json, write_text
from ml_product.modelling.xgboost_model import train_xgboost


@dataclass(frozen=True)
class ModelTrainingResult:
    manifest: dict[str, Any]
    candidate_recommendation: dict[str, Any]
    validation_metrics: dict[str, Any]
    test_metrics: dict[str, Any]
    candidate_directory: Path
    report_directory: Path


def train_models(
    config: ModelTrainingConfig,
    threshold_config: ThresholdConfig,
    *,
    feature_dir: Path | None = None,
    candidate_dir: Path | None = None,
    report_dir: Path | None = None,
    replace: bool = False,
) -> ModelTrainingResult:
    candidates_path = config.candidate_directory(candidate_dir)
    reports_path = config.report_directory(report_dir)
    prepare_directory(candidates_path, replace=replace)
    reports_path.mkdir(parents=True, exist_ok=True)
    data = load_model_data(config, feature_dir, reports_path)
    training_fingerprint = config_fingerprint(config, threshold_config)
    train_y = data.splits["train"].target.to_numpy(dtype=bool)
    validation_y = data.splits["validation"].target.to_numpy(dtype=bool)
    test_y = data.splits["test"].target.to_numpy(dtype=bool)
    train_prevalence = float(train_y.mean())
    validation_prevalence = float(validation_y.mean())
    model_records = _train_candidates(config, data, candidates_path, training_fingerprint)
    baseline_metrics = _evaluate_baselines(
        data,
        threshold_config,
        train_prevalence=train_prevalence,
        validation_prevalence=validation_prevalence,
    )
    validation_rows: list[dict[str, Any]] = []
    calibration_report: dict[str, Any] = {}
    threshold_report: dict[str, Any] = {}
    global_explainability: dict[str, dict[str, Any]] = {}
    calibrated_probabilities: dict[str, dict[str, np.ndarray]] = {}
    calibrators: dict[str, Calibrator] = {}
    fitted_records = [record for record in model_records if record["training_status"] == "fitted"]
    for record in fitted_records:
        validation_prob = record["validation_probability"]
        threshold_seed = analyse_thresholds(
            validation_y,
            validation_prob,
            threshold_config,
            prevalence=validation_prevalence,
        )
        calibrator, calibration = select_calibration(
            validation_y,
            validation_prob,
            threshold=threshold_seed["selected_threshold"],
            prevalence=validation_prevalence,
            config=config,
        )
        calibrators[record["model_family"]] = calibrator
        validation_calibrated = calibrator.transform(validation_prob)
        test_calibrated = calibrator.transform(record["test_probability"])
        threshold = analyse_thresholds(
            validation_y,
            validation_calibrated,
            threshold_config,
            prevalence=validation_prevalence,
        )
        metrics = evaluate_predictions(
            validation_y,
            validation_calibrated,
            threshold=threshold["selected_threshold"],
            prevalence=validation_prevalence,
        )
        validation_rows.append(
            _comparison_row(record, metrics, threshold, calibration["selected_method"])
        )
        calibration_report[record["model_family"]] = calibration
        threshold_report[record["model_family"]] = threshold
        global_explainability[record["model_family"]] = build_global_explainability(
            model=record["model"],
            model_family=record["model_family"],
            feature_names=data.feature_names,
            validation_features=data.splits["validation"].features,
            validation_target=validation_y,
            model_metadata=record["metadata"],
            config=config,
        )
        calibrated_probabilities[record["model_family"]] = {
            "validation": validation_calibrated,
            "test": test_calibrated,
        }
    comparison_rows = [*baseline_metrics["validation_rows"], *validation_rows]
    recommendation = recommend_candidate(
        comparison_rows,
        prevalence_brier=baseline_metrics["prevalence_validation"]["brier_score"],
        config=config,
    )
    selected_family = recommendation["recommended_model"] or "logistic_regression"
    selected_record = next(
        item for item in fitted_records if item["model_family"] == selected_family
    )
    selected_threshold = threshold_report[selected_family]["selected_threshold"]
    selected_calibration = calibration_report[selected_family]["selected_method"]
    test_metrics = evaluate_predictions(
        test_y,
        calibrated_probabilities[selected_family]["test"],
        threshold=selected_threshold,
        prevalence=float(test_y.mean()),
        bootstrap_seed=config.evaluation.bootstrap_seed,
        bootstrap_iterations=config.evaluation.bootstrap_iterations,
    )
    validation_selected_metrics = next(
        row for row in validation_rows if row["model_family"] == selected_family
    )
    recommendation.update(
        {
            "recommended_calibration": selected_calibration,
            "selected_threshold": selected_threshold,
            "selection_rule": "validation-only deterministic candidate and threshold selection",
            "test_set_used_for_selection": False,
            "registration_readiness": "candidate_evidence_ready_for_future_review",
            "approval_status": "not_granted",
            "deployment_status": "not_performed",
            "known_risks": [
                "small synthetic validation and test sets",
                "high positive-class prevalence",
                "subgroup metrics are exploratory and unstable",
            ],
        }
    )
    feature_importance, local_explanations = build_explainability(
        model=selected_record["model"],
        model_family=selected_family,
        feature_names=data.feature_names,
        validation_features=data.splits["validation"].features,
        validation_target=validation_y,
        test_features=data.splits["test"].features,
        test_target=test_y,
        test_identifiers=data.splits["test"].identifiers,
        test_probabilities=calibrated_probabilities[selected_family]["test"],
        threshold=selected_threshold,
        model_metadata=selected_record["metadata"],
        config=config,
    )
    feature_importance["candidate_global_importance"] = global_explainability
    feature_importance["principal_candidate"] = selected_family
    fairness = build_fairness_report(
        features=data.splits["test"].features,
        target=test_y,
        probabilities=calibrated_probabilities[selected_family]["test"],
        threshold=selected_threshold,
        preprocessor_metadata=data.preprocessor_metadata,
        minimum_group_size=config.fairness.minimum_group_size,
    )
    manifest = _manifest(
        config=config,
        threshold_config=threshold_config,
        data=data,
        training_fingerprint=training_fingerprint,
        model_records=model_records,
    )
    _write_candidate_bundle(
        candidates_path,
        selected_record,
        calibrators[selected_family],
        recommendation,
        data.feature_names,
        training_fingerprint,
        data.manifest["feature_build_identifier"],
    )
    evidence_payload = {
        "candidate_recommendation": recommendation,
        "validation_metrics": {"rows": comparison_rows},
        "test_metrics": {
            "test_set_used_for_selection": False,
            "test_set_evaluated_after_selection": True,
            "selected_model": selected_family,
            "metrics": test_metrics,
            "baseline_references": baseline_metrics["test_references"],
        },
    }
    _write_evidence(
        reports_path,
        manifest=manifest,
        baseline_metrics=baseline_metrics,
        validation_rows=comparison_rows,
        test_metrics=evidence_payload["test_metrics"],
        comparison=comparison_payload(comparison_rows, recommendation["selection_rule"]),
        threshold_analysis=threshold_report[selected_family],
        calibration_report={
            **calibration_report[selected_family],
            "test_calibration_results": test_metrics,
        },
        feature_importance=feature_importance,
        local_explanations=local_explanations,
        fairness=fairness,
        recommendation=recommendation,
        report_payload=evidence_payload,
    )
    return ModelTrainingResult(
        manifest=manifest,
        candidate_recommendation=recommendation,
        validation_metrics={"rows": comparison_rows, "selected": validation_selected_metrics},
        test_metrics=evidence_payload["test_metrics"],
        candidate_directory=candidates_path,
        report_directory=reports_path,
    )


def _train_candidates(
    config: ModelTrainingConfig,
    data: ModelData,
    candidates_path: Path,
    training_fingerprint: str,
) -> list[dict[str, Any]]:
    train_x = data.splits["train"].features
    train_y = data.splits["train"].target.to_numpy(dtype=bool)
    validation_x = data.splits["validation"].features
    test_x = data.splits["test"].features
    records: list[dict[str, Any]] = []
    trainers = [
        (
            "logistic_regression",
            config.models.logistic_regression.enabled,
            train_logistic_regression,
        ),
        ("random_forest", config.models.random_forest.enabled, train_random_forest),
        ("xgboost", config.models.xgboost.enabled, train_xgboost),
    ]
    for family, enabled, trainer in trainers:
        if not enabled:
            continue
        started = time.perf_counter()
        candidate_id = semantic_model_identifier(
            family, data.manifest["feature_build_identifier"], training_fingerprint
        )
        try:
            model, metadata = trainer(train_x, train_y, config)
        except Exception as exc:
            if family == "xgboost":
                raise RuntimeError(
                    "Configured XGBoost candidate failed to train. Install a compatible "
                    "OpenMP runtime such as Homebrew libomp on macOS, then rerun Milestone "
                    "6 training."
                ) from exc
            raise
        runtime = time.perf_counter() - started
        artifact = candidates_path / (
            f"{family}.json" if family == "xgboost" else f"{family}.joblib"
        )
        if family == "xgboost":
            model.save_model(artifact)
        else:
            write_joblib(artifact, model)
        records.append(
            {
                "model_family": family,
                "candidate_identifier": candidate_id,
                "training_status": "fitted",
                "model": model,
                "metadata": metadata,
                "artifact_location": str(Path("models/candidate") / artifact.name),
                "runtime_seconds": round(runtime, 6),
                "validation_probability": predict_probability(model, validation_x),
                "test_probability": predict_probability(model, test_x),
            }
        )
    return records


def _evaluate_baselines(
    data: ModelData,
    threshold_config: ThresholdConfig,
    *,
    train_prevalence: float,
    validation_prevalence: float,
) -> dict[str, Any]:
    train_y = data.splits["train"].target.to_numpy(dtype=bool)
    validation_y = data.splits["validation"].target.to_numpy(dtype=bool)
    test_y = data.splits["test"].target.to_numpy(dtype=bool)
    prevalence = fit_prevalence_baseline(train_y)
    majority = fit_majority_baseline(train_y)
    rows = []
    test_refs: dict[str, Any] = {}
    for baseline in (prevalence, majority):
        validation_prob = baseline.predict_proba(len(validation_y))
        threshold = analyse_thresholds(
            validation_y,
            validation_prob,
            threshold_config,
            prevalence=validation_prevalence,
        )
        metrics = evaluate_predictions(
            validation_y,
            validation_prob,
            threshold=threshold["selected_threshold"],
            prevalence=validation_prevalence,
        )
        rows.append(
            {
                "model_family": baseline.identifier,
                "model_type": "baseline",
                "selected_threshold": threshold["selected_threshold"],
                "selected_calibration": "not_applicable",
                "weighted_cost": threshold["selected_row"]["total_weighted_cost"],
                **_metric_subset(metrics),
            }
        )
        test_refs[baseline.identifier] = evaluate_predictions(
            test_y,
            baseline.predict_proba(len(test_y)),
            threshold=threshold["selected_threshold"],
            prevalence=float(test_y.mean()),
        )
    return {
        "training_prevalence": train_prevalence,
        "majority_class": bool(majority.majority_class),
        "validation_rows": rows,
        "test_references": test_refs,
        "prevalence_validation": rows[0],
    }


def _comparison_row(
    record: dict[str, Any],
    metrics: dict[str, Any],
    threshold: dict[str, Any],
    calibration: str,
) -> dict[str, Any]:
    return {
        "model_family": record["model_family"],
        "model_type": "candidate",
        "candidate_identifier": record["candidate_identifier"],
        "selected_threshold": threshold["selected_threshold"],
        "selected_calibration": calibration,
        "weighted_cost": threshold["selected_row"]["total_weighted_cost"],
        "runtime_seconds": record["runtime_seconds"],
        "model_complexity": record["model_family"],
        "explainability_level": (
            "high" if record["model_family"] == "logistic_regression" else "medium"
        ),
        **_metric_subset(metrics),
    }


def _metric_subset(metrics: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "roc_auc",
        "pr_auc",
        "pr_auc_lift_over_prevalence",
        "brier_score",
        "log_loss",
        "recall",
        "precision",
        "specificity",
        "f1",
        "balanced_accuracy",
        "calibration_error",
        "accuracy",
    ]
    return {key: metrics[key] for key in keys}


def _manifest(
    *,
    config: ModelTrainingConfig,
    threshold_config: ThresholdConfig,
    data: ModelData,
    training_fingerprint: str,
    model_records: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "experiment_name": config.experiment.name,
        "generated_at_utc": timestamp_utc(),
        "training_configuration_fingerprint": training_fingerprint,
        "feature_build_identifier": data.manifest["feature_build_identifier"],
        "feature_configuration_fingerprint": data.manifest["feature_configuration_fingerprint"],
        "source_fingerprint": data.manifest["source_fingerprint"],
        "database_build_identifier": data.manifest["database_build_identifier"],
        "random_seed": config.experiment.random_seed,
        "model_families": [record["model_family"] for record in model_records],
        "library_versions": _library_versions(),
        "feature_count": len(data.feature_names),
        "split_counts": {
            split: len(split_data.target) for split, split_data in data.splits.items()
        },
        "candidate_identifiers": {
            record["model_family"]: record["candidate_identifier"] for record in model_records
        },
        "candidate_training_status": {
            record["model_family"]: {
                "training_status": record["training_status"],
                "fit_status": record.get("metadata", {}).get("fit_status"),
                "artifact_location": record.get("artifact_location"),
                "failure_reason": record.get("failure_reason"),
            }
            for record in model_records
        },
        "test_set_used_for_selection": False,
        "test_set_evaluated_after_selection": True,
        "synthetic_data_declaration": "All modelling data are synthetic.",
        "threshold_config": threshold_config.model_dump(mode="json"),
    }


def _library_versions() -> dict[str, str]:
    try:
        import xgboost

        xgboost_version = xgboost.__version__
    except Exception as exc:
        xgboost_version = f"unavailable: {exc}"

    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "joblib": joblib.__version__,
        "xgboost": xgboost_version,
    }


def _write_candidate_bundle(
    candidates_path: Path,
    selected_record: dict[str, Any],
    calibrator: Calibrator,
    recommendation: dict[str, Any],
    feature_names: list[str],
    training_fingerprint: str,
    feature_build_identifier: str,
) -> None:
    calibrator_path = candidates_path / "calibrator.joblib"
    write_joblib(calibrator_path, calibrator)
    write_json(
        candidates_path / "candidate_bundle.json",
        {
            "candidate_status": "recommended_for_registration_review",
            "not_production_model": True,
            "selected_model": selected_record["model_family"],
            "selected_artifact": selected_record["artifact_location"],
            "calibrator_artifact": "models/candidate/calibrator.joblib",
            "feature_names": feature_names,
            "feature_build_identifier": feature_build_identifier,
            "training_configuration_fingerprint": training_fingerprint,
            "recommendation": recommendation,
        },
    )


def _write_evidence(
    reports_path: Path,
    *,
    manifest: dict[str, Any],
    baseline_metrics: dict[str, Any],
    validation_rows: list[dict[str, Any]],
    test_metrics: dict[str, Any],
    comparison: dict[str, Any],
    threshold_analysis: dict[str, Any],
    calibration_report: dict[str, Any],
    feature_importance: dict[str, Any],
    local_explanations: dict[str, Any],
    fairness: dict[str, Any],
    recommendation: dict[str, Any],
    report_payload: dict[str, Any],
) -> None:
    write_json(reports_path / "model_training_manifest.json", manifest)
    write_json(reports_path / "baseline_metrics.json", baseline_metrics)
    write_json(reports_path / "validation_metrics.json", {"rows": validation_rows})
    write_json(reports_path / "test_metrics.json", test_metrics)
    write_json(reports_path / "model_comparison.json", comparison)
    write_json(reports_path / "threshold_analysis.json", threshold_analysis)
    write_json(reports_path / "calibration_report.json", calibration_report)
    write_json(reports_path / "feature_importance.json", feature_importance)
    write_json(reports_path / "local_explanations.json", local_explanations)
    write_json(reports_path / "fairness_report.json", fairness)
    write_json(reports_path / "candidate_recommendation.json", recommendation)
    write_text(reports_path / "model_evaluation_report.md", evaluation_report(report_payload))
    write_text(reports_path / "model_card.md", model_card(report_payload))
