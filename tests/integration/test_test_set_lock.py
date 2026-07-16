import json
from pathlib import Path


def test_test_set_lock_is_recorded() -> None:
    manifest = json.loads(
        Path("reports/model_evaluation/model_training_manifest.json").read_text(encoding="utf-8")
    )
    recommendation = json.loads(
        Path("reports/model_evaluation/candidate_recommendation.json").read_text(encoding="utf-8")
    )
    assert manifest["test_set_used_for_selection"] is False
    assert recommendation["test_set_used_for_selection"] is False
