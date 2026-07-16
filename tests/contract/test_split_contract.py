import json
from pathlib import Path


def test_split_contract() -> None:
    summary = json.loads(
        Path("reports/model_evaluation/split_summary.json").read_text(encoding="utf-8")
    )
    assert summary["patient_overlap_count"] == 0
    assert summary["admission_overlap_count"] == 0
    assert all(
        summary["splits"][split]["row_count"] > 0 for split in ("train", "validation", "test")
    )
    assert summary["split_fingerprint"]
