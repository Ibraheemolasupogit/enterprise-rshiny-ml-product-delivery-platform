import json
from pathlib import Path


def test_calibration_contract() -> None:
    payload = json.loads(
        Path("reports/model_evaluation/calibration_report.json").read_text(encoding="utf-8")
    )
    assert payload["method_eligibility"]["isotonic"]["eligible"] is False
    assert payload["selected_method"] in {"uncalibrated", "sigmoid"}
