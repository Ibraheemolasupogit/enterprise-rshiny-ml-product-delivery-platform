"""Audit event creation."""

from __future__ import annotations

from ml_product.registry.metadata import timestamp_utc
from ml_product.registry.models import AuditEvent


def audit_event(
    *,
    event_type: str,
    model_name: str,
    registry_version: int,
    actor: str,
    details: dict[str, str] | None = None,
) -> AuditEvent:
    return AuditEvent(
        event_type=event_type,
        model_name=model_name,
        registry_version=registry_version,
        timestamp_utc=timestamp_utc(),
        actor=actor,
        details=details or {},
    )
