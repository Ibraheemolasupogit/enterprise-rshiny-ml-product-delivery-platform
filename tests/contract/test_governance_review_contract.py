import json
from pathlib import Path


def test_governance_review_contains_test_weaknesses() -> None:
    payload = json.loads(
        Path("reports/model_evaluation/governance_review.json").read_text(encoding="utf-8")
    )
    assert payload["recommended_decision"] == "defer"
    codes = {flag["code"] for flag in payload["review_flags"]}
    assert "weak_test_specificity" in codes
    assert "small_test_set" in codes
    assert payload["human_decision_required"] is True
