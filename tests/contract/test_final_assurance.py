import json
import subprocess
import sys
from pathlib import Path


def test_final_assurance_make_target_exists() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert "final-assurance:" in makefile
    assert "$(PYTHON) scripts/final_assurance.py" in makefile


def test_final_assurance_plan_is_checkout_safe_and_credential_free() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/final_assurance.py", "--plan"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["offline_safe_by_default"] is True
    assert payload["requires_credentials"] is False
    commands = [" ".join(step["command"]) for step in payload["steps"]]
    combined = "\n".join(commands)
    assert "postgres-" not in combined
    assert "denodo-" not in combined
    assert "sas" not in combined.lower()
    assert "activate-model" not in combined
    assert "record-approval-decision" not in combined


def test_final_assurance_optional_live_steps_are_explicitly_opt_in() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/final_assurance.py", "--plan", "--include-live"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    names = {step["name"] for step in payload["steps"]}
    assert "postgresql_readiness" in names
    assert "denodo_readiness" in names


def test_final_assurance_report_schema_preserves_governance_boundaries() -> None:
    payload = json.loads(Path("reports/assurance/final_assurance.json").read_text())

    assert payload["schema_version"] == "final-assurance-report/v1"
    assert payload["offline_safe_by_default"] is True
    assert payload["credentials_required"] is False
    assert payload["optional_live_integrations"]["sas_viya"] == "requires_external_environment"
    assert payload["overall_outcome"] in {"not_run", "passed", "failed"}


def test_final_assurance_plan_contains_required_reconstruction_and_lifecycle_steps() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/final_assurance.py", "--plan"],
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    names = {step["name"] for step in payload["steps"]}

    assert "clean_checkout_review_artifact_reconstruction" in names
    assert "offline_lifecycle_orchestration" in names
    assert "lifecycle_evidence_checksum" in names
    assert "lifecycle_resume" in names
    assert "release_assurance" in names
