import json
from pathlib import Path


def test_serving_contract() -> None:
    contract = json.loads(
        Path("reports/model_evaluation/serving_contract.json").read_text(encoding="utf-8")
    )
    readiness = json.loads(
        Path("reports/model_evaluation/serving_readiness.json").read_text(encoding="utf-8")
    )
    assert contract["input_contract"] == "raw_admission_time_predictors"
    assert contract["outcome_fields_rejected"] is True
    assert contract["database_queries_for_prediction"] is False
    assert readiness["approved_serving"] is False
    assert readiness["production_deployment"] is False
