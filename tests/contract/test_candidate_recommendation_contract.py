import json
from pathlib import Path


def test_candidate_recommendation_contract() -> None:
    payload = json.loads(
        Path("reports/model_evaluation/candidate_recommendation.json").read_text(encoding="utf-8")
    )
    assert payload["recommendation_status"] == "recommended_for_registration_review"
    assert payload["approval_status"] == "not_granted"
    assert payload["deployment_status"] == "not_performed"
