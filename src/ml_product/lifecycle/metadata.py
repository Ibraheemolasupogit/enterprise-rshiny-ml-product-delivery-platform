"""Lifecycle metadata mapping and reconciliation."""

from __future__ import annotations

from typing import Any, cast

from ml_product.lifecycle.identity import registration_fingerprint
from ml_product.lifecycle.models import ReconciliationResult, ReconciliationStatus
from ml_product.lifecycle.package import ModelLifecyclePackage

SUPPORTED_METADATA_FIELDS = {
    "model_name",
    "model_version",
    "model_family",
    "target_column",
    "prediction_point",
    "dataset_version",
    "source_fingerprint",
    "feature_count",
    "selected_threshold",
    "selected_calibration",
    "registry_status",
    "synthetic_data_declaration",
    "local_registry_id",
    "candidate_identifier",
    "registration_fingerprint",
}


def build_sas_viya_metadata(package: ModelLifecyclePackage) -> dict[str, Any]:
    fingerprint = registration_fingerprint(package)
    custom_properties = {
        "target_column": package.target.get("column"),
        "prediction_point": package.target.get("prediction_point"),
        "dataset_version": package.source.get("dataset_version"),
        "source_fingerprint": package.source.get("source_fingerprint"),
        "feature_count": package.feature_metadata.get("feature_count"),
        "selected_threshold": package.threshold_calibration_metadata.get(
            "selected_threshold"
        ),
        "selected_calibration": package.threshold_calibration_metadata.get(
            "selected_calibration"
        ),
        "registry_status": package.governance_status.get("registry_status"),
        "synthetic_data_declaration": package.synthetic_data_declaration,
        "local_registry_id": package.registry_id,
        "candidate_identifier": package.candidate_identifier,
        "registration_fingerprint": fingerprint,
    }
    return {
        "model": {
            "name": package.model_name,
            "description": "Python-generated long-stay admission risk model.",
            "customProperties": {
                "local_registry_id": package.registry_id,
                "candidate_identifier": package.candidate_identifier,
            },
        },
        "version": {
            "name": f"v{package.model_version:06d}",
            "modelType": package.model_family,
            "registrationFingerprint": fingerprint,
            "customProperties": {
                **custom_properties,
                "model_sha256": package.artefacts.get("model_sha256"),
                "calibrator_sha256": package.artefacts.get("calibrator_sha256"),
            },
        },
        "metadata": {
            "customProperties": custom_properties,
            "metrics": {
                "evaluation": package.evaluation_metrics.get("registry_summary", {}),
                "locked_test": package.evaluation_metrics.get("locked_test", {}),
            },
            "fairness": package.fairness_summary,
            "thresholdCalibration": package.threshold_calibration_metadata,
            "governance": package.governance_status,
        },
    }


def comparable_metadata(package: ModelLifecyclePackage) -> dict[str, Any]:
    metadata = build_sas_viya_metadata(package)["metadata"]["customProperties"]
    return {key: metadata[key] for key in sorted(SUPPORTED_METADATA_FIELDS) if key in metadata}


def reconcile_metadata(
    package: ModelLifecyclePackage,
    external_metadata: dict[str, Any],
) -> ReconciliationResult:
    local = comparable_metadata(package)
    external = _external_custom_properties(external_metadata)
    matched: dict[str, Any] = {}
    mismatches: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for key, local_value in local.items():
        if key not in external:
            missing.append(key)
        elif external[key] == local_value:
            matched[key] = local_value
        else:
            mismatches[key] = {"local": local_value, "external": external[key]}
    status: ReconciliationStatus = "matched"
    if mismatches:
        status = "mismatch"
    elif missing:
        status = "missing_external"
    return ReconciliationResult(
        status=status,
        matched_fields=matched,
        mismatches=mismatches,
        missing_external_fields=missing,
        unsupported_fields=sorted(
            set(build_sas_viya_metadata(package)["metadata"]) - {"customProperties"}
        ),
    )


def _external_custom_properties(payload: dict[str, Any]) -> dict[str, Any]:
    if "customProperties" in payload and isinstance(payload["customProperties"], dict):
        return cast(dict[str, Any], payload["customProperties"])
    if "metadata" in payload and isinstance(payload["metadata"], dict):
        metadata = payload["metadata"]
        if isinstance(metadata.get("customProperties"), dict):
            return cast(dict[str, Any], metadata["customProperties"])
    return {}
