import json
import subprocess
import sys
from pathlib import Path

import yaml

from ml_product.lifecycle.config import LifecycleConfig, WorkflowConfig


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ml_product.cli", *args],
        check=False,
        text=True,
        capture_output=True,
    )


def test_lifecycle_describe_provider_cli() -> None:
    result = run_cli("lifecycle-describe-provider")

    assert result.returncode == 0
    assert "Selected provider: local" in result.stdout


def test_lifecycle_check_readiness_cli() -> None:
    result = run_cli("lifecycle-check-readiness")

    assert result.returncode == 0
    assert "healthy=True" in result.stdout


def test_lifecycle_build_model_package_cli_does_not_mutate_registry(tmp_path: Path) -> None:
    registry_path = Path("models/registry.json")
    before = registry_path.read_text(encoding="utf-8")
    output_path = tmp_path / "lifecycle-package.json"

    result = run_cli("lifecycle-build-model-package", "--output-path", str(output_path))

    assert result.returncode == 0, result.stderr
    assert output_path.is_file()
    assert "Built lifecycle package for long_stay_admission_risk:1" in result.stdout
    assert registry_path.read_text(encoding="utf-8") == before


def test_lifecycle_register_model_dry_run_cli_does_not_mutate_registry() -> None:
    registry_path = Path("models/registry.json")
    before = registry_path.read_text(encoding="utf-8")

    result = run_cli("lifecycle-register-model", "--dry-run")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["provider"] == "local"
    assert payload["registration_status"] == "already_registered"
    assert registry_path.read_text(encoding="utf-8") == before


def test_lifecycle_show_and_reconcile_registration_cli() -> None:
    show = run_cli("lifecycle-show-registration")
    reconcile = run_cli("lifecycle-reconcile-registration")

    assert show.returncode == 0, show.stderr
    assert json.loads(show.stdout)["provider"] == "local"
    assert reconcile.returncode == 0, reconcile.stderr
    assert json.loads(reconcile.stdout)["status"] == "matched"


def test_lifecycle_promotion_cli_smoke_commands() -> None:
    commands = (
        ("lifecycle-show-champion",),
        ("lifecycle-list-challengers",),
        ("lifecycle-compare-champion",),
        ("lifecycle-assess-promotion", "--dry-run"),
        ("lifecycle-show-promotion",),
        ("lifecycle-reconcile-promotion",),
    )

    for command in commands:
        result = run_cli(*command)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)


def test_lifecycle_orchestration_cli_smoke_commands(tmp_path: Path) -> None:
    config_path = _temporary_workflow_config(tmp_path)

    run = run_cli(
        "lifecycle-run-end-to-end",
        "--config",
        str(config_path),
        "--mode",
        "enterprise_dry_run",
        "--dry-run",
        "--json",
    )
    assert run.returncode == 0, run.stderr
    payload = json.loads(run.stdout)
    assert payload["mode"] == "enterprise_dry_run"
    assert payload["mutation_flags"] == {
        "allow_external_registration": False,
        "allow_external_promotion": False,
        "allow_local_activation": False,
    }

    commands = (
        ("lifecycle-show-workflow", "--json"),
        ("lifecycle-resume-workflow", "--mode", "enterprise_dry_run", "--json"),
        ("lifecycle-validate-workflow-evidence", "--json"),
    )
    for command in commands:
        result = run_cli(*command, "--config", str(config_path))
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)


def _temporary_workflow_config(tmp_path: Path) -> Path:
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml")).model_copy(
        update={
            "workflow": WorkflowConfig(
                state_path=tmp_path / "workflow-state.json",
                evidence_directory=tmp_path / "workflow-evidence",
            )
        }
    )
    path = tmp_path / "model_lifecycle.yaml"
    path.write_text(
        yaml.safe_dump(config.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    return path
