import json
from pathlib import Path


def test_candidate_bundle_contains_feature_schema() -> None:
    bundle = json.loads(
        (Path("models/candidate") / "candidate_bundle.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        Path("reports/model_evaluation/model_training_manifest.json").read_text(encoding="utf-8")
    )
    assert len(bundle["feature_names"]) == manifest["feature_count"]
    assert bundle["not_production_model"] is True
    assert (Path("models/candidate") / "xgboost.json").is_file()
    assert manifest["candidate_identifiers"]["xgboost"].startswith("CAND-")
