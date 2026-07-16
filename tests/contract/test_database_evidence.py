import json
from pathlib import Path


def test_database_evidence_files_exist_and_are_local() -> None:
    required = [
        "database_build_manifest.json",
        "database_validation.json",
        "linkage_quality.json",
        "curated_view_summary.json",
        "database_build_report.md",
    ]

    for file_name in required:
        path = Path("reports/data_quality") / file_name
        assert path.is_file(), path
        text = path.read_text(encoding="utf-8")
        assert "/Users/" not in text
        assert "real_denodo" not in text


def test_database_evidence_counts_match_expected_sample() -> None:
    payload = json.loads(Path("reports/data_quality/database_build_manifest.json").read_text())

    assert payload["provider"] == "denodo_compatible_local"
    assert payload["commercial_tool_evidence"] is False
    assert payload["counts"]["quality.data_quality_issues"] == 9
