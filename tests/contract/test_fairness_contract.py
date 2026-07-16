import json
from pathlib import Path


def test_fairness_contract() -> None:
    payload = json.loads(
        Path("reports/model_evaluation/fairness_report.json").read_text(encoding="utf-8")
    )
    assert set(payload["groups"]) == {"sex", "age_band", "deprivation_group"}
    assert payload["limitations"]
