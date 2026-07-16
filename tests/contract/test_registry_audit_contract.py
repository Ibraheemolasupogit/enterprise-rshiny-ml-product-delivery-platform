import json
from pathlib import Path


def test_registry_audit_contract() -> None:
    payload = json.loads(
        Path("reports/model_evaluation/registry_audit_summary.json").read_text(encoding="utf-8")
    )
    assert payload["event_count"] >= 1
    assert payload["events"][0]["event_type"] == "candidate_registered"
