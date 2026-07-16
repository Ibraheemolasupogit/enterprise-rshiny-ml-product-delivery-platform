"""Validate Milestone 6 model-development evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ml_product.modelling.config import ModelTrainingConfig

REQUIRED_EVIDENCE = [
    "model_training_manifest.json",
    "baseline_metrics.json",
    "validation_metrics.json",
    "test_metrics.json",
    "model_comparison.json",
    "threshold_analysis.json",
    "calibration_report.json",
    "feature_importance.json",
    "local_explanations.json",
    "fairness_report.json",
    "candidate_recommendation.json",
    "model_evaluation_report.md",
    "model_card.md",
]


def validate_model_outputs(config: ModelTrainingConfig) -> dict[str, Any]:
    report_dir = config.report_directory()
    errors: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    for name in REQUIRED_EVIDENCE:
        path = report_dir / name
        if not path.is_file():
            errors.append(f"Missing model evidence: {name}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "/Users/" in text:
            errors.append(f"Model evidence contains an absolute user path: {name}")
        if name.endswith(".json"):
            payloads[name] = json.loads(text)
    recommendation = payloads.get("candidate_recommendation.json", {})
    if recommendation.get("test_set_used_for_selection") is not False:
        errors.append("Candidate recommendation must record test_set_used_for_selection=false.")
    if recommendation.get("approval_status") != "not_granted":
        errors.append("Candidate recommendation must not grant approval.")
    manifest = payloads.get("model_training_manifest.json", {})
    if manifest.get("test_set_used_for_selection") is not False:
        errors.append("Training manifest must lock test set out of selection.")
    if manifest.get("feature_count") != config.feature_source.expected_feature_count:
        errors.append("Training manifest feature count mismatch.")
    xgboost_status = manifest.get("candidate_training_status", {}).get("xgboost", {})
    if xgboost_status.get("training_status") != "fitted":
        errors.append("XGBoost candidate must train successfully for Milestone 6 completion.")
    if xgboost_status.get("fit_status") != "fitted":
        errors.append("XGBoost fit status must be fitted.")
    if xgboost_status.get("artifact_location") != "models/candidate/xgboost.json":
        errors.append(
            "XGBoost candidate artefact must be recorded as models/candidate/xgboost.json."
        )
    comparison = payloads.get("model_comparison.json", {})
    comparison_families = {row.get("model_family") for row in comparison.get("rows", [])}
    if "xgboost" not in comparison_families:
        errors.append("Model comparison must include XGBoost validation metrics.")
    feature_importance = payloads.get("feature_importance.json", {})
    xgboost_importance = feature_importance.get("candidate_global_importance", {}).get("xgboost")
    if not xgboost_importance or not xgboost_importance.get("permutation_importance"):
        errors.append("Feature-importance evidence must include XGBoost permutation importance.")
    if not xgboost_importance or not xgboost_importance.get("native_importance"):
        errors.append("Feature-importance evidence must include XGBoost native importance.")
    calibration = payloads.get("calibration_report.json", {})
    isotonic = calibration.get("method_eligibility", {}).get("isotonic", {})
    if isotonic.get("eligible") is True:
        errors.append("Isotonic calibration should be blocked for the small validation set.")
    for path in (Path("models/approved"), Path("models/archived")):
        if any(item.name != ".gitkeep" for item in path.iterdir()):
            errors.append(f"No approved/archive model artefacts allowed in {path}.")
    return {"valid": not errors, "errors": errors}
