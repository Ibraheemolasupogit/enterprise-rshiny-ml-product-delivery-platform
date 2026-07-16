import pytest

from ml_product.registry.models import validate_transition


def test_valid_transition_allows_registration_review() -> None:
    validate_transition("registered", "approval_pending")


def test_invalid_transition_rejects_candidate_to_active() -> None:
    with pytest.raises(ValueError, match="candidate -> active"):
        validate_transition("candidate", "active")
