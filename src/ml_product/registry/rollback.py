"""Rollback validation for registry versions."""

from __future__ import annotations

from ml_product.registry.metadata import timestamp_utc
from ml_product.registry.models import ModelVersion, RollbackEvent


def build_rollback_event(
    *,
    target: ModelVersion,
    actor: str,
    reason: str,
    dry_run: bool,
) -> RollbackEvent:
    if target.status not in {"approved", "active", "retired"}:
        raise ValueError("Rollback target must be an approved-compatible version.")
    return RollbackEvent(
        actor=actor,
        target_version=target.registry_version,
        rolled_back_at_utc=timestamp_utc(),
        reason=reason,
        dry_run=dry_run,
    )
