"""Candidate registration validation and model-version construction."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from ml_product.registry.compatibility import validate_feature_contract, validate_test_lock
from ml_product.registry.config import GovernanceConfig, RegistryConfig
from ml_product.registry.governance import build_governance_review
from ml_product.registry.metadata import (
    registry_identifier,
    sha256_file,
    stable_fingerprint,
    timestamp_utc,
)
from ml_product.registry.models import (
    ArtefactReference,
    EvaluationSummary,
    FeatureContract,
    ModelVersion,
    PreprocessorContract,
)
from ml_product.registry.storage import read_json


def build_model_version(
    *,
    root: Path,
    config: RegistryConfig,
    governance_config: GovernanceConfig,
    candidate_identifier: str,
    registry_version: int,
    model_config_path: Path,
    candidate_dir: Path,
    registered_model_path: str,
    registered_calibrator_path: str,
    model_checksum: str,
    calibrator_checksum: str,
) -> ModelVersion:
    report_dir = root / "reports/model_evaluation"
    manifest = read_json(report_dir / "model_training_manifest.json")
    recommendation = read_json(report_dir / "candidate_recommendation.json")
    validation = read_json(report_dir / "validation_metrics.json")
    test = read_json(report_dir / "test_metrics.json")
    leakage = read_json(report_dir / "leakage_report.json")
    fairness = read_json(report_dir / "fairness_report.json")
    preprocessor = read_json(report_dir / "preprocessor_metadata.json")
    bundle = read_json(candidate_dir / "candidate_bundle.json")
    validate_test_lock(manifest, recommendation)
    if recommendation.get("recommended_model") != "xgboost":
        raise ValueError("Milestone 7 registration expects the recommended XGBoost candidate.")
    if manifest["candidate_identifiers"]["xgboost"] != candidate_identifier:
        raise ValueError("Candidate identifier does not match model training manifest.")
    if bundle["feature_build_identifier"] != manifest["feature_build_identifier"]:
        raise ValueError("Candidate bundle feature build identifier mismatch.")
    feature_names = list(bundle["feature_names"])
    validate_feature_contract(
        feature_names=feature_names,
        preprocessor_metadata=preprocessor,
        expected_count=manifest["feature_count"],
    )
    validation_row = _validation_row(validation, "xgboost")
    governance = build_governance_review(
        policy=governance_config,
        validation_row=validation_row,
        test_metrics=test,
        leakage_report=leakage,
        fairness_report=fairness,
        feature_schema_match=True,
        reproducibility_passed=config.registration.require_reproducibility_pass,
    )
    evidence_fingerprint = stable_fingerprint(
        {
            "manifest": manifest,
            "recommendation": recommendation,
            "validation_row": validation_row,
            "test": test,
            "governance": governance.model_dump(mode="json"),
        }
    )
    return ModelVersion(
        model_name=manifest["experiment_name"],
        registry_id=registry_identifier(registry_version),
        registry_version=registry_version,
        status="registered",
        model_family="xgboost",
        candidate_identifier=candidate_identifier,
        calibration=recommendation["recommended_calibration"],
        threshold=float(recommendation["selected_threshold"]),
        artefacts=ArtefactReference(
            model_path=registered_model_path,
            calibrator_path=registered_calibrator_path,
            model_sha256=model_checksum,
            calibrator_sha256=calibrator_checksum,
        ),
        feature_contract=FeatureContract(
            feature_count=len(feature_names),
            feature_names=feature_names,
            feature_schema_fingerprint=stable_fingerprint(feature_names),
            feature_build_identifier=manifest["feature_build_identifier"],
        ),
        preprocessor_contract=PreprocessorContract(
            preprocessor_fingerprint=preprocessor["semantic_fingerprint"],
            preprocessor_checksum=sha256_file(report_dir / "preprocessor_metadata.json"),
            source_path="reports/model_evaluation/preprocessor_metadata.json",
        ),
        evaluation_summary=EvaluationSummary(
            validation_pr_auc=float(validation_row["pr_auc"]),
            validation_brier_score=float(validation_row["brier_score"]),
            validation_recall=float(validation_row["recall"]),
            validation_precision=float(validation_row["precision"]),
            test_pr_auc=float(test["metrics"]["pr_auc"]),
            test_roc_auc=float(test["metrics"]["roc_auc"]),
            test_brier_score=float(test["metrics"]["brier_score"]),
            test_recall=float(test["metrics"]["recall"]),
            test_specificity=float(test["metrics"]["specificity"]),
            test_balanced_accuracy=float(test["metrics"]["balanced_accuracy"]),
            test_set_used_for_selection=bool(test["test_set_used_for_selection"]),
        ),
        governance=governance,
        created_at_utc=timestamp_utc(),
        training_configuration_fingerprint=manifest["training_configuration_fingerprint"],
        evidence_fingerprint=evidence_fingerprint,
        synthetic_data_declaration=manifest["synthetic_data_declaration"],
    )


def _validation_row(validation: dict[str, Any], model_family: str) -> dict[str, Any]:
    for row in validation["rows"]:
        if row["model_family"] == model_family:
            return cast(dict[str, Any], row)
    raise ValueError(f"Missing validation row for {model_family}.")
