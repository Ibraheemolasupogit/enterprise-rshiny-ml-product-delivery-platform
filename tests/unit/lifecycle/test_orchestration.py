from pathlib import Path
from typing import Any

import pytest

from ml_product.lifecycle.config import LifecycleConfig, WorkflowConfig
from ml_product.lifecycle.factory import build_lifecycle_provider
from ml_product.lifecycle.models import RegistrationResult
from ml_product.lifecycle.orchestration import (
    STAGE_ORDER,
    run_lifecycle_workflow,
    validate_workflow_evidence,
)
from ml_product.lifecycle.package import ModelLifecyclePackage


def test_lifecycle_workflow_local_safe_preserves_stage_order_and_mutation_gates(
    tmp_path: Path,
) -> None:
    config = _workflow_config(tmp_path)
    provider = build_lifecycle_provider(config)
    registry_path = Path("models/registry.json")
    registry_before = registry_path.read_text(encoding="utf-8")

    run = run_lifecycle_workflow(config, provider, mode="local_safe")

    assert [stage.stage_id for stage in run.stages] == STAGE_ORDER
    assert run.summary is not None
    assert run.summary.status == "blocked"
    assert _stage(run, "registration").status == "passed"
    assert _stage(run, "external_promotion").status == "skipped"
    assert _stage(run, "local_activation").status == "skipped"
    assert _stage(run, "local_activation").outputs["local_activation_performed"] is False
    assert run.mutation_flags == {
        "allow_external_registration": False,
        "allow_external_promotion": False,
        "allow_local_activation": False,
    }
    assert registry_path.read_text(encoding="utf-8") == registry_before


def test_lifecycle_workflow_enterprise_dry_run_does_not_enable_mutation_flags(
    tmp_path: Path,
) -> None:
    config = _workflow_config(tmp_path)
    provider = build_lifecycle_provider(config)

    run = run_lifecycle_workflow(
        config,
        provider,
        mode="enterprise_dry_run",
        allow_external_registration=True,
        allow_external_promotion=True,
        allow_local_activation=True,
    )

    assert run.mode == "enterprise_dry_run"
    assert run.mutation_flags == {
        "allow_external_registration": False,
        "allow_external_promotion": False,
        "allow_local_activation": False,
    }
    assert _stage(run, "external_promotion").status == "skipped"
    assert _stage(run, "local_activation").outputs["local_activation_performed"] is False


def test_lifecycle_workflow_records_blocked_and_failed_stages(tmp_path: Path) -> None:
    config = _workflow_config(tmp_path)

    run = run_lifecycle_workflow(
        config,
        FailingRegistrationProvider(),
        mode="local_safe",
        selected_stages={"registration"},
    )

    assert run.summary is not None
    assert run.summary.status == "failed"
    failed_stage = _stage(run, "registration")
    assert failed_stage.status == "failed"
    assert failed_stage.failure is not None
    assert failed_stage.failure.error_type == "RuntimeError"


def test_lifecycle_workflow_evidence_checksum_and_credential_boundary(
    tmp_path: Path,
) -> None:
    config = _workflow_config(tmp_path)
    provider = build_lifecycle_provider(config)

    run = run_lifecycle_workflow(config, provider, mode="local_safe")
    validation = validate_workflow_evidence(config)

    assert validation == {"valid": True, "errors": []}
    assert run.evidence_bundle_path is not None
    evidence = (Path.cwd() / run.evidence_bundle_path).read_text(encoding="utf-8")
    assert "SAS_VIYA_ACCESS_TOKEN" not in evidence
    assert "SAS_VIYA_CLIENT_SECRET" not in evidence
    assert "POSTGRES_PASSWORD" not in evidence


def test_lifecycle_workflow_resume_reuses_completed_stages(tmp_path: Path) -> None:
    config = _workflow_config(tmp_path)
    provider = build_lifecycle_provider(config)
    first = run_lifecycle_workflow(config, provider, mode="local_safe")

    resumed = run_lifecycle_workflow(config, provider, mode="local_safe", resume=True)

    assert resumed.workflow_id == first.workflow_id
    assert _stage(resumed, "registration").status == "resumed"
    assert _stage(resumed, "promotion_assessment").status != "resumed"


def test_lifecycle_workflow_resume_rejects_material_fingerprint_change(
    tmp_path: Path,
) -> None:
    config = _workflow_config(tmp_path)
    provider = build_lifecycle_provider(config)
    run_lifecycle_workflow(config, provider, mode="local_safe")
    changed = config.model_copy(
        update={
            "workflow": WorkflowConfig(
                state_path=config.workflow.state_path,
                evidence_directory=tmp_path / "different-evidence",
            )
        }
    )

    with pytest.raises(ValueError, match="material configuration change"):
        run_lifecycle_workflow(changed, provider, mode="local_safe", resume=True)


def test_lifecycle_workflow_identifiers_are_deterministic(tmp_path: Path) -> None:
    config = _workflow_config(tmp_path)
    provider = build_lifecycle_provider(config)

    first = run_lifecycle_workflow(config, provider, mode="local_safe")
    second = run_lifecycle_workflow(config, provider, mode="local_safe")

    assert second.workflow_id == first.workflow_id
    assert second.configuration_fingerprint == first.configuration_fingerprint
    assert second.package_fingerprint == first.package_fingerprint


def test_lifecycle_makefile_exposes_orchestration_targets() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    for target in (
        "lifecycle-e2e-local:",
        "lifecycle-e2e-dry-run:",
        "lifecycle-e2e-show:",
        "lifecycle-e2e-validate:",
    ):
        assert target in makefile


def _workflow_config(tmp_path: Path) -> LifecycleConfig:
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml"))
    return config.model_copy(
        update={
            "workflow": WorkflowConfig(
                state_path=tmp_path / "workflow-state.json",
                evidence_directory=tmp_path / "workflow-evidence",
            )
        }
    )


def _stage(run: Any, stage_id: str) -> Any:
    return next(stage for stage in run.stages if stage.stage_id == stage_id)


class FailingRegistrationProvider:
    provider_name = "failing"

    def register_model_package(
        self,
        package: ModelLifecyclePackage,
        *,
        dry_run: bool = False,
    ) -> RegistrationResult:
        del package, dry_run
        raise RuntimeError("forced registration failure")

    def readiness_check(self) -> dict[str, Any]:
        return {"healthy": True}

    def retrieve_model_metadata(self, model_name: str, version: int) -> dict[str, Any]:
        return {"model_name": model_name, "version": version}

    def submit_lifecycle_status(
        self,
        model_name: str,
        version: int,
        status: str,
        *,
        actor: str,
        reason: str,
    ) -> dict[str, Any]:
        del model_name, version, status, actor, reason
        return {}

    def promote_model_version(
        self,
        model_name: str,
        version: int,
        *,
        actor: str,
        reason: str,
    ) -> dict[str, Any]:
        del model_name, version, actor, reason
        return {}
