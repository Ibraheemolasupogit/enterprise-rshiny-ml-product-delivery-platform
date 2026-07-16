import json
from pathlib import Path


def test_leakage_report_contract() -> None:
    report = json.loads(
        Path("reports/model_evaluation/leakage_report.json").read_text(encoding="utf-8")
    )
    assert report["total_violations"] == 0
    assert report["direct_leakage_violations"] == []
    assert report["temporal_leakage_violations"] == []
    assert report["identifier_leakage_violations"] == []
    assert report["group_leakage_violations"] == []
