"""Serving readiness helpers."""

from __future__ import annotations

from ml_product.serving.loader import LoadedModel


def readiness_payload(loaded: LoadedModel | None) -> dict[str, object]:
    if loaded is None:
        return {
            "ready": False,
            "reason": "no_active_approved_model",
            "review_mode": False,
        }
    return {
        "ready": True,
        "reason": "review_mode" if loaded.review_mode else "active_approved_model",
        "review_mode": loaded.review_mode,
        "model_name": loaded.version.model_name,
        "registry_version": loaded.version.registry_version,
    }
