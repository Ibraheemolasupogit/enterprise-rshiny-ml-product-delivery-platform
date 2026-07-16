import json
from pathlib import Path


def test_model_training_manifest_contract() -> None:
    manifest = json.loads(
        Path("reports/model_evaluation/model_training_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["feature_count"] == 71
    assert manifest["test_set_used_for_selection"] is False
    assert "logistic_regression" in manifest["candidate_identifiers"]
    xgboost = manifest["candidate_training_status"]["xgboost"]
    assert xgboost["training_status"] == "fitted"
    assert xgboost["fit_status"] == "fitted"
    assert xgboost["artifact_location"] == "models/candidate/xgboost.json"
