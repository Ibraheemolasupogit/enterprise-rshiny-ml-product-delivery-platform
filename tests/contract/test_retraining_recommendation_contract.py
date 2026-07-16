import json
from pathlib import Path


def test_retraining_recommendation_contract() -> None:
    payload = json.loads(
        Path("reports/retraining/retraining_recommendation.json").read_text(encoding="utf-8")
    )
    assert payload["approval_status"] == "not_granted"
    assert payload["activation_status"] == "inactive"
    assert payload["deployment_status"] == "not_performed"
    assert payload["historical_test_set_used_for_selection"] is False
    assert payload["automatic_action"] == "none"
    assert payload["human_review_required"] is True
