import json
from pathlib import Path


def test_feature_registry_contract() -> None:
    registry = json.loads(
        Path("reports/model_evaluation/feature_registry.json").read_text(encoding="utf-8")
    )
    assert registry["coverage_valid"] is True
    assert registry["stable_ordering_valid"] is True
    assert registry["registry_entry_count"] == registry["output_feature_count"]
    names = [entry["feature_name"] for entry in registry["features"]]
    assert len(names) == len(set(names))
