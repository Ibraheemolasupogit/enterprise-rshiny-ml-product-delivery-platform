import json
from pathlib import Path


def test_registry_and_retraining_states_remain_controlled() -> None:
    registry = json.loads(Path("models/registry.json").read_text(encoding="utf-8"))
    retraining = json.loads(
        Path("reports/retraining/retraining_recommendation.json").read_text(encoding="utf-8")
    )
    version = registry["models"][0]["versions"][0]
    assert version["registry_version"] == 1
    assert version["approval_decision"] is None
    assert version["activation_event"] is None
    assert retraining["recommendation"] == "retain_champion"
    assert retraining["automatic_action"] == "none"
