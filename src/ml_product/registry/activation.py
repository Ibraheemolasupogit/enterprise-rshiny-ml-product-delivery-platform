"""Activation controls for approved registry versions."""

from __future__ import annotations

from ml_product.registry.metadata import timestamp_utc
from ml_product.registry.models import ActivationEvent, ModelVersion


def build_activation_event(
    *,
    version: ModelVersion,
    actor: str,
    reason: str,
    previous_active_version: int | None,
) -> ActivationEvent:
    if version.status != "approved":
        raise ValueError("Only approved models can be activated.")
    return ActivationEvent(
        actor=actor,
        activated_at_utc=timestamp_utc(),
        previous_active_version=previous_active_version,
        reason=reason,
    )
