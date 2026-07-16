import json
from pathlib import Path


def test_release_readiness_contract() -> None:
    payload = json.loads(
        Path("reports/assurance/release_readiness.json").read_text(encoding="utf-8")
    )
    assert payload["local_review_readiness"] == "ready_for_local_review"
    assert payload["operational_release_readiness"] == "blocked_for_operational_release"
    assert payload["model_approval_state"] == "pending"
    assert payload["model_activation_state"] == "inactive"
    assert payload["external_deployment_state"] == "not_performed"
