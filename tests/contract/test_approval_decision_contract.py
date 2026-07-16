import json
from pathlib import Path


def test_approval_decision_contract() -> None:
    payload = json.loads(
        Path("reports/model_evaluation/approval_decision.json").read_text(encoding="utf-8")
    )
    assert payload["decision"] == "pending"
    assert payload["approval_status"] == "pending"
    assert payload["automatic_approval"] is False
