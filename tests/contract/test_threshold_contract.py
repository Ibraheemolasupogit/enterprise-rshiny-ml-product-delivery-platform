import json
from pathlib import Path


def test_threshold_contract() -> None:
    payload = json.loads(
        Path("reports/model_evaluation/threshold_analysis.json").read_text(encoding="utf-8")
    )
    assert payload["selected_threshold"] in [row["threshold"] for row in payload["thresholds"]]
    assert payload["selection_rule"]
