"""Approval decision helpers."""

from __future__ import annotations

from ml_product.registry.metadata import timestamp_utc
from ml_product.registry.models import ApprovalDecision, ApprovalDecisionValue, RegistryState


def build_approval_decision(
    *,
    decision: ApprovalDecisionValue,
    actor: str,
    reason: str,
    conditions: list[str],
    evidence_fingerprint: str,
    previous_status: RegistryState,
) -> ApprovalDecision:
    return ApprovalDecision(
        decision=decision,
        actor=actor,
        reason=reason,
        conditions=conditions,
        evidence_fingerprint=evidence_fingerprint,
        decided_at_utc=timestamp_utc(),
        previous_status=previous_status,
    )
