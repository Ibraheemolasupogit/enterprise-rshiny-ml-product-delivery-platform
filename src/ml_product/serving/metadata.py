"""Safe model metadata for API responses."""

from __future__ import annotations

from ml_product.serving.loader import LoadedModel


def model_metadata(loaded: LoadedModel | None) -> dict[str, object]:
    if loaded is None:
        return {"available": False, "reason": "no_active_approved_model"}
    approval_status = (
        "pending"
        if loaded.version.approval_decision is None
        else loaded.version.approval_decision.decision
    )
    return {
        "available": True,
        "model_name": loaded.version.model_name,
        "registry_version": loaded.version.registry_version,
        "candidate_identifier": loaded.version.candidate_identifier,
        "model_family": loaded.version.model_family,
        "calibration": loaded.version.calibration,
        "threshold": loaded.version.threshold,
        "approval_status": approval_status,
        "activation_status": loaded.version.status,
        "review_mode": loaded.review_mode,
    }
