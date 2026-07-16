"""Verify deterministic Milestone 6 model-development builds."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from ml_product.features.builder import build_features
from ml_product.features.config import FeatureConfig
from ml_product.ingestion.build import build_database
from ml_product.ingestion.config import DatabaseConfig
from ml_product.modelling.config import ModelTrainingConfig, ThresholdConfig
from ml_product.modelling.metadata import stable_payload
from ml_product.modelling.training import train_models
from ml_product.utils.paths import repository_root


def main() -> int:
    root = repository_root()
    database_config = DatabaseConfig.from_file(root / "config/database.yaml")
    feature_config = FeatureConfig.from_file(root / "config/features.yaml")
    model_config = ModelTrainingConfig.from_file(root / "config/model_training.yaml")
    threshold_config = ThresholdConfig.from_file(root / "config/model_thresholds.yaml")
    with tempfile.TemporaryDirectory(prefix="model-build-") as tmp:
        tmp_path = Path(tmp)
        database = build_database(
            database_config.with_overrides(
                database_path=tmp_path / "ml_product.duckdb",
                replace=True,
            )
        )
        first_reports = tmp_path / "reports-a"
        second_reports = tmp_path / "reports-b"
        first_features = tmp_path / "features-a"
        second_features = tmp_path / "features-b"
        build_features(
            feature_config,
            database_path=database.database_path,
            output_dir=first_features,
            evidence_dir=first_reports,
            replace=True,
        )
        build_features(
            feature_config,
            database_path=database.database_path,
            output_dir=second_features,
            evidence_dir=second_reports,
            replace=True,
        )
        first = train_models(
            model_config,
            threshold_config,
            feature_dir=first_features,
            candidate_dir=tmp_path / "candidate-a",
            report_dir=first_reports,
            replace=True,
        )
        second = train_models(
            model_config,
            threshold_config,
            feature_dir=second_features,
            candidate_dir=tmp_path / "candidate-b",
            report_dir=second_reports,
            replace=True,
        )
        _assert_equal(stable_payload(first.manifest), stable_payload(second.manifest))
        _assert_xgboost_fitted(first.manifest, tmp_path / "candidate-a" / "xgboost.json")
        _assert_xgboost_fitted(second.manifest, tmp_path / "candidate-b" / "xgboost.json")
        _assert_equal(first.candidate_recommendation, second.candidate_recommendation)
        _assert_close(
            _without_volatile(first.validation_metrics),
            _without_volatile(second.validation_metrics),
        )
        _assert_close(first.test_metrics, second.test_metrics)
        first_importance = _load_json(first_reports / "feature_importance.json")
        second_importance = _load_json(second_reports / "feature_importance.json")
        _assert_close(first_importance, second_importance)
        first_comparison = _load_json(first_reports / "model_comparison.json")
        _assert_xgboost_in_comparison(first_comparison)
        if first.candidate_recommendation["test_set_used_for_selection"] is not False:
            raise AssertionError("Test-set selection flag must remain false.")
    print("Model build reproducibility verified, including fitted XGBoost evidence.")
    return 0


def _assert_equal(left: Any, right: Any) -> None:
    if left != right:
        raise AssertionError("Stable model-build evidence differed.")


def _assert_close(left: Any, right: Any) -> None:
    if isinstance(left, dict) and isinstance(right, dict):
        for key in left:
            _assert_close(left[key], right[key])
    elif isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            raise AssertionError("List lengths differ.")
        for left_item, right_item in zip(left, right, strict=True):
            _assert_close(left_item, right_item)
    elif isinstance(left, float) or isinstance(right, float):
        if not np.isclose(float(left), float(right), atol=1e-10, rtol=1e-10, equal_nan=True):
            raise AssertionError(f"Float values differ: {left} != {right}")
    else:
        if left != right:
            raise AssertionError(f"Values differ: {left} != {right}")


def _without_volatile(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {
            key: _without_volatile(value)
            for key, value in payload.items()
            if key not in {"runtime_seconds"}
        }
    if isinstance(payload, list):
        return [_without_volatile(item) for item in payload]
    return payload


def _load_json(path: Path) -> dict[str, Any]:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{path} must contain a JSON object.")
    return payload


def _assert_xgboost_fitted(manifest: dict[str, Any], artifact: Path) -> None:
    status = manifest["candidate_training_status"]["xgboost"]
    if status.get("training_status") != "fitted" or status.get("fit_status") != "fitted":
        raise AssertionError("XGBoost must be fitted for reproducible Milestone 6 evidence.")
    if status.get("artifact_location") != "models/candidate/xgboost.json":
        raise AssertionError("XGBoost artefact location must be stable.")
    if not artifact.is_file():
        raise AssertionError("XGBoost candidate artefact was not created.")


def _assert_xgboost_in_comparison(comparison: dict[str, Any]) -> None:
    rows = [row for row in comparison.get("rows", []) if row.get("model_family") == "xgboost"]
    if len(rows) != 1:
        raise AssertionError("Model comparison must include exactly one XGBoost row.")


if __name__ == "__main__":
    raise SystemExit(main())
