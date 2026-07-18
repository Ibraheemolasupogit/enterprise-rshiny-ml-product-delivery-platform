"""Model lifecycle package builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field

from ml_product.lifecycle.config import LifecycleConfig
from ml_product.modelling.config import ModelTrainingConfig
from ml_product.registry.config import GovernanceConfig, RegistryConfig
from ml_product.registry.registry import LocalModelRegistry
from ml_product.utils.paths import repository_root


class ModelLifecyclePackage(BaseModel):
    """Portable model package contract for future lifecycle providers."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "model-lifecycle-package/v1"
    provider_contract: dict[str, Any]
    model_name: str
    model_version: int
    registry_id: str
    candidate_identifier: str
    model_family: str
    calibration: str
    threshold: float
    created_at_utc: str
    target: dict[str, Any]
    source: dict[str, Any]
    feature_metadata: dict[str, Any]
    evaluation_metrics: dict[str, Any]
    fairness_summary: dict[str, Any]
    threshold_calibration_metadata: dict[str, Any]
    artefacts: dict[str, Any]
    governance_status: dict[str, Any]
    synthetic_data_declaration: str
    evidence_fingerprint: str
    training_configuration_fingerprint: str
    referenced_evidence: dict[str, str] = Field(default_factory=dict)


def build_model_package(
    config: LifecycleConfig,
    *,
    root: Path | None = None,
) -> ModelLifecyclePackage:
    """Build a deterministic review package from committed/generated evidence."""

    repo_root = (root or repository_root()).resolve()
    package_config = config.model_package
    training_config = ModelTrainingConfig.from_file(repo_root / package_config.model_config_path)
    registry = LocalModelRegistry(
        RegistryConfig.from_file(repo_root / package_config.registry_config),
        GovernanceConfig.from_file(repo_root / package_config.governance_config),
        root=repo_root,
    )
    version = registry.get_model_version(
        package_config.model_name,
        package_config.registry_version,
    )
    report_directory = _resolve(repo_root, package_config.report_directory)
    feature_manifest = _read_report(report_directory, "feature_build_manifest.json")
    feature_registry = _read_report(report_directory, "feature_registry.json")
    test_metrics = _read_report(report_directory, "test_metrics.json")
    validation_metrics = _read_report(report_directory, "validation_metrics.json")
    fairness_report = _read_report(report_directory, "fairness_report.json")
    calibration_report = _read_report(report_directory, "calibration_report.json")
    threshold_analysis = _read_report(report_directory, "threshold_analysis.json")
    candidate_recommendation = _read_report(report_directory, "candidate_recommendation.json")
    training_manifest = _read_report(report_directory, "model_training_manifest.json")

    return ModelLifecyclePackage(
        provider_contract={
            "selected_provider": config.provider.selected,
            "local_provider_label": config.local.provider_label,
            "sas_viya_provider_label": config.sas_viya.provider_label,
            "live_sas_viya_enabled": config.provider.selected == "sas_viya"
            and config.sas_viya.enabled,
        },
        model_name=version.model_name,
        model_version=version.registry_version,
        registry_id=version.registry_id,
        candidate_identifier=version.candidate_identifier,
        model_family=version.model_family,
        calibration=version.calibration,
        threshold=version.threshold,
        created_at_utc=version.created_at_utc,
        target={
            "column": training_config.experiment.target_column,
            "positive_class": training_config.experiment.positive_class,
            "prediction_point": training_config.experiment.prediction_point,
        },
        source={
            "view": feature_manifest.get("source_view"),
            "provider": feature_manifest.get("source_provider"),
            "source_fingerprint": feature_manifest.get("source_fingerprint"),
            "dataset_version": feature_manifest.get("dataset_version"),
            "eligible_row_count": feature_manifest.get("counts", {}).get("eligible_row_count"),
        },
        feature_metadata={
            "feature_build_identifier": version.feature_contract.feature_build_identifier,
            "feature_count": version.feature_contract.feature_count,
            "feature_schema_fingerprint": version.feature_contract.feature_schema_fingerprint,
            "feature_names": version.feature_contract.feature_names,
            "preprocessor": version.preprocessor_contract.model_dump(mode="json"),
            "feature_registry": {
                "output_feature_count": feature_registry.get("output_feature_count"),
                "schema_fingerprint": feature_registry.get("schema_fingerprint"),
            },
        },
        evaluation_metrics={
            "registry_summary": version.evaluation_summary.model_dump(mode="json"),
            "locked_test": test_metrics.get("metrics", {}),
            "validation": _selected_validation_row(validation_metrics, version.model_family),
            "test_set_used_for_selection": candidate_recommendation.get(
                "test_set_used_for_selection"
            ),
        },
        fairness_summary={
            "minimum_group_size": fairness_report.get("minimum_group_size"),
            "groups": _summarise_fairness_groups(fairness_report),
            "limitations": version.governance.informational_limitations,
        },
        threshold_calibration_metadata={
            "selected_threshold": threshold_analysis.get("selected_threshold"),
            "selection_rule": threshold_analysis.get("selection_rule"),
            "selected_threshold_row": threshold_analysis.get("selected_row"),
            "selected_calibration": calibration_report.get("selected_method"),
            "calibration_selection_reason": calibration_report.get("selection_reason"),
        },
        artefacts=version.artefacts.model_dump(mode="json"),
        governance_status={
            "registry_status": version.status,
            "approval_decision": None
            if version.approval_decision is None
            else version.approval_decision.model_dump(mode="json"),
            "activation_event": None
            if version.activation_event is None
            else version.activation_event.model_dump(mode="json"),
            "recommended_decision": version.governance.recommended_decision,
            "human_decision_required": version.governance.human_decision_required,
            "hard_requirements": version.governance.hard_requirements,
            "review_flags": version.governance.review_flags,
            "registration_allowed": True,
            "approval_granted": False,
            "activation_status": "inactive",
        },
        synthetic_data_declaration=version.synthetic_data_declaration,
        evidence_fingerprint=version.evidence_fingerprint,
        training_configuration_fingerprint=version.training_configuration_fingerprint,
        referenced_evidence={
            "model_training_manifest": _relative(
                repo_root, report_directory / "model_training_manifest.json"
            ),
            "candidate_recommendation": _relative(
                repo_root, report_directory / "candidate_recommendation.json"
            ),
            "test_metrics": _relative(repo_root, report_directory / "test_metrics.json"),
            "validation_metrics": _relative(
                repo_root, report_directory / "validation_metrics.json"
            ),
            "fairness_report": _relative(repo_root, report_directory / "fairness_report.json"),
            "calibration_report": _relative(
                repo_root, report_directory / "calibration_report.json"
            ),
            "threshold_analysis": _relative(
                repo_root, report_directory / "threshold_analysis.json"
            ),
            "feature_build_manifest": _relative(
                repo_root, report_directory / "feature_build_manifest.json"
            ),
            "training_manifest_identifier": str(
                training_manifest.get("training_run_identifier", "")
            ),
        },
    )


def write_model_package(package: ModelLifecyclePackage, output_path: Path) -> Path:
    destination = _resolve(repository_root(), output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        package.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    return destination


def _read_report(directory: Path, file_name: str) -> dict[str, Any]:
    payload = json.loads((directory / file_name).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{file_name} must contain a JSON object.")
    return payload


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _relative(root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def _selected_validation_row(payload: dict[str, Any], model_family: str) -> dict[str, Any]:
    for row in payload.get("rows", []):
        if isinstance(row, dict) and row.get("model_family") == model_family:
            return cast(dict[str, Any], row)
    return {}


def _summarise_fairness_groups(payload: dict[str, Any]) -> dict[str, Any]:
    groups = payload.get("groups", {})
    if not isinstance(groups, dict):
        return {}
    return {
        str(group_name): {
            "row_count": len(rows) if isinstance(rows, list) else 0,
            "suppressed_count": sum(
                1 for row in rows if isinstance(row, dict) and row.get("suppressed")
            )
            if isinstance(rows, list)
            else 0,
        }
        for group_name, rows in groups.items()
    }
