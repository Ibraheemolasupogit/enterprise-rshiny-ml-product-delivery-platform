import json
from pathlib import Path


def test_remote_ci_pre_push_evidence_does_not_fabricate_runs() -> None:
    payload = json.loads(
        Path("reports/assurance/remote_ci_validation.json").read_text(encoding="utf-8")
    )
    if payload["remote_ci_executed"]:
        for workflow in payload["workflows"]:
            assert workflow["run_id"]
            assert workflow["run_url"].startswith("https://github.com/")
            assert workflow["status"] == "completed"
            assert workflow["conclusion"] == "success"
    else:
        assert payload["workflows"] == []
        assert "pre-push" in payload["reason"]
