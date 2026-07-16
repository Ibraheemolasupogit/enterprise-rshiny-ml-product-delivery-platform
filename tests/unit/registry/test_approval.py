import pytest

from ml_product.registry.approval import build_approval_decision


def test_conditional_approval_requires_conditions() -> None:
    with pytest.raises(ValueError, match="Conditional approval"):
        build_approval_decision(
            decision="approve_with_conditions",
            actor="LOCAL-GOVERNANCE-REVIEWER",
            reason="Needs conditions",
            conditions=[],
            evidence_fingerprint="abc",
            previous_status="approval_pending",
        )


def test_defer_decision_records_actor_and_reason() -> None:
    decision = build_approval_decision(
        decision="defer",
        actor="LOCAL-GOVERNANCE-REVIEWER",
        reason="Synthetic evidence requires review.",
        conditions=[],
        evidence_fingerprint="abc",
        previous_status="approval_pending",
    )
    assert decision.decision == "defer"
    assert decision.actor == "LOCAL-GOVERNANCE-REVIEWER"
