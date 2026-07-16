"""Record genuine GitHub Actions run evidence for Milestone 14."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
GH_RUN_LIST_SOURCE = (
    "gh run list --json "
    "databaseId,name,workflowName,status,conclusion,event,headSha,url,createdAt,updatedAt"
)


def write_json(path: str, payload: dict[str, Any]) -> None:
    destination = ROOT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str, text: str) -> None:
    destination = ROOT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text.strip() + "\n", encoding="utf-8")


def normalise_run(run: dict[str, Any]) -> dict[str, Any]:
    run_id = run.get("databaseId") or run.get("run_id")
    url = run.get("url") or run.get("run_url")
    if not run_id or not isinstance(url, str) or not url.startswith("https://github.com/"):
        raise ValueError("Each remote CI run must include a GitHub run ID and URL.")
    return {
        "run_id": run_id,
        "run_url": url,
        "name": run.get("name") or run.get("workflowName") or "unknown",
        "workflow_name": run.get("workflowName") or run.get("name") or "unknown",
        "event": run.get("event"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "head_sha": run.get("headSha") or run.get("head_sha"),
        "created_at": run.get("createdAt") or run.get("created_at"),
        "updated_at": run.get("updatedAt") or run.get("updated_at"),
    }


def build_payload(runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not runs:
        raise ValueError("Remote CI evidence requires at least one GitHub Actions run.")
    workflows = [normalise_run(run) for run in runs]
    completed = all(item["status"] == "completed" for item in workflows)
    passed = completed and all(item["conclusion"] == "success" for item in workflows)
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "remote_ci_executed": True,
        "remote_ci_passed": passed,
        "source": GH_RUN_LIST_SOURCE,
        "workflows": workflows,
        "summary": {
            "workflow_count": len(workflows),
            "completed": completed,
            "successful": passed,
            "head_shas": sorted({str(item["head_sha"]) for item in workflows if item["head_sha"]}),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# Remote CI Validation",
        "",
        "Remote CI executed: `true`",
        f"Remote CI passed: `{str(payload['remote_ci_passed']).lower()}`",
        "",
    ]
    for workflow in payload["workflows"]:
        lines.append(
            f"- {workflow['workflow_name']}: `{workflow['conclusion']}` ({workflow['run_url']})"
        )
    write_text("reports/assurance/remote_ci_validation.md", "\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--runs-json",
        required=True,
        help="Path to JSON output from gh run list for the pushed commit.",
    )
    args = parser.parse_args()
    runs = json.loads(Path(args.runs_json).read_text(encoding="utf-8"))
    if not isinstance(runs, list):
        raise ValueError("--runs-json must contain a JSON list.")
    payload = build_payload(runs)
    write_json("reports/assurance/remote_ci_validation.json", payload)
    write_markdown(payload)


if __name__ == "__main__":
    main()
