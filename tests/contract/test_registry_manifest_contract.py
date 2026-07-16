import json
from pathlib import Path


def test_registry_manifest_contract() -> None:
    payload = json.loads(
        Path("reports/model_evaluation/model_registry_manifest.json").read_text(encoding="utf-8")
    )
    assert payload["candidate_identifier"] == "CAND-85EA9202CAD6FE7F"
    assert payload["registry_state"] == "registered"
    assert payload["approval_state"] == "pending"
    assert payload["activation_state"] == "inactive"
    assert payload["feature_count"] == 71
