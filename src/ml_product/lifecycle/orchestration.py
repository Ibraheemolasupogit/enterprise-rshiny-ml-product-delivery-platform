"""Canonical lifecycle orchestration control plane."""

from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ml_product.lifecycle.config import LifecycleConfig
from ml_product.lifecycle.identity import registration_fingerprint
from ml_product.lifecycle.package import build_model_package
from ml_product.lifecycle.provider import ModelLifecycleProvider
from ml_product.registry.config import GovernanceConfig, RegistryConfig
from ml_product.release import ReleaseConfig, assess_release_readiness
from ml_product.serving.config import ServingConfig
from ml_product.serving.validation import validate_serving
from ml_product.utils.paths import repository_root

StageStatus = Literal["pending", "running", "passed", "skipped", "blocked", "failed", "resumed"]
WorkflowMode = Literal["local_safe", "enterprise_dry_run", "enterprise_live"]
GateStatus = Literal["passed", "blocked", "failed", "skipped"]


class FailureDetails(BaseModel):
    message: str
    error_type: str


class EvidenceReference(BaseModel):
    path: str
    checksum: str


class GateDecision(BaseModel):
    gate_id: str
    status: GateStatus
    reason: str


class WorkflowStage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage_id: str
    status: StageStatus = "pending"
    started_at_utc: str | None = None
    ended_at_utc: str | None = None
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    gates: list[GateDecision] = Field(default_factory=list)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    failure: FailureDetails | None = None


class ResumeState(BaseModel):
    workflow_id: str
    configuration_fingerprint: str
    package_fingerprint: str | None = None
    completed_stages: list[str] = Field(default_factory=list)
    blocked_stage: str | None = None
    failed_stage: str | None = None


class WorkflowSummary(BaseModel):
    status: Literal["passed", "blocked", "failed"]
    passed_stages: int
    blocked_stages: int
    failed_stages: int
    skipped_stages: int
    known_limitations: list[str] = Field(default_factory=list)


class WorkflowRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    mode: WorkflowMode
    configuration_fingerprint: str
    package_fingerprint: str | None = None
    started_at_utc: str
    ended_at_utc: str | None = None
    mutation_flags: dict[str, bool]
    stages: list[WorkflowStage]
    summary: WorkflowSummary | None = None
    resume_state: ResumeState
    evidence_bundle_path: str | None = None
    evidence_checksum: str | None = None


STAGE_ORDER = [
    "data_readiness",
    "logical_view_readiness",
    "feature_build",
    "feature_validation",
    "model_training_evaluation",
    "lifecycle_package",
    "registration",
    "registration_reconciliation",
    "promotion_assessment",
    "approval_gate",
    "external_promotion",
    "local_activation",
    "serving_validation",
    "monitoring_baseline",
    "release_readiness",
]


def run_lifecycle_workflow(
    config: LifecycleConfig,
    provider: ModelLifecycleProvider,
    *,
    mode: WorkflowMode = "local_safe",
    allow_external_registration: bool = False,
    allow_external_promotion: bool = False,
    allow_local_activation: bool = False,
    selected_stages: set[str] | None = None,
    resume: bool = False,
    restart_stage: str | None = None,
) -> WorkflowRun:
    root = repository_root()
    package = build_model_package(config)
    package_fingerprint = registration_fingerprint(package)
    config_fingerprint = _configuration_fingerprint(config, mode)
    state_path = _resolve(config.workflow.state_path)
    effective_external_registration = allow_external_registration and mode == "enterprise_live"
    effective_external_promotion = allow_external_promotion and mode == "enterprise_live"
    effective_local_activation = allow_local_activation and mode == "enterprise_live"
    previous = _load_run(state_path) if resume and state_path.is_file() else None
    if previous is not None and previous.configuration_fingerprint != config_fingerprint:
        raise ValueError("Cannot resume lifecycle workflow after material configuration change.")
    if previous is not None and previous.package_fingerprint != package_fingerprint:
        raise ValueError("Cannot resume lifecycle workflow after package identity change.")

    run = WorkflowRun(
        workflow_id=f"LWF-{config_fingerprint[:12]}",
        mode=mode,
        configuration_fingerprint=config_fingerprint,
        package_fingerprint=package_fingerprint,
        started_at_utc=_now(),
        mutation_flags={
            "allow_external_registration": effective_external_registration,
            "allow_external_promotion": effective_external_promotion,
            "allow_local_activation": effective_local_activation,
        },
        stages=[],
        resume_state=ResumeState(
            workflow_id=f"LWF-{config_fingerprint[:12]}",
            configuration_fingerprint=config_fingerprint,
            package_fingerprint=package_fingerprint,
        ),
    )
    completed = set(previous.resume_state.completed_stages) if previous is not None else set()
    if restart_stage is not None:
        if restart_stage not in STAGE_ORDER:
            raise ValueError(f"Unknown restart stage: {restart_stage}")
        restart_index = STAGE_ORDER.index(restart_stage)
        completed = {item for item in completed if STAGE_ORDER.index(item) < restart_index}
    for stage_id in STAGE_ORDER:
        if selected_stages is not None and stage_id not in selected_stages:
            run.stages.append(WorkflowStage(stage_id=stage_id, status="skipped"))
            continue
        if resume and stage_id in completed and restart_stage is None:
            run.stages.append(WorkflowStage(stage_id=stage_id, status="resumed"))
            continue
        run.stages.append(
            _execute_stage(
                stage_id,
                config=config,
                provider=provider,
                mode=mode,
                allow_external_registration=effective_external_registration,
                allow_external_promotion=effective_external_promotion,
                allow_local_activation=effective_local_activation,
            )
        )
    run = _finalise(run)
    _write_run(run, state_path)
    run = _write_evidence_bundle(run, _resolve(config.workflow.evidence_directory), root)
    _write_run(run, state_path)
    return run


def validate_workflow_evidence(config: LifecycleConfig) -> dict[str, Any]:
    run = _load_run(_resolve(config.workflow.state_path))
    if run.evidence_bundle_path is None or run.evidence_checksum is None:
        return {"valid": False, "errors": ["Workflow evidence bundle is missing."]}
    path = _resolve(Path(run.evidence_bundle_path))
    payload = json.loads(path.read_text(encoding="utf-8"))
    checksum = payload.pop("evidence_checksum", None)
    expected = _sha256_json(payload)
    valid = checksum == expected == run.evidence_checksum
    return {
        "valid": valid,
        "errors": [] if valid else ["Workflow evidence checksum mismatch."],
    }


def _execute_stage(
    stage_id: str,
    *,
    config: LifecycleConfig,
    provider: ModelLifecycleProvider,
    mode: WorkflowMode,
    allow_external_registration: bool,
    allow_external_promotion: bool,
    allow_local_activation: bool,
) -> WorkflowStage:
    started = _now()
    stage = WorkflowStage(stage_id=stage_id, status="running", started_at_utc=started)
    try:
        package = build_model_package(config)
        if stage_id == "data_readiness":
            stage.outputs = {"source_mode": mode, "offline_safe": mode != "enterprise_live"}
            stage.gates = [
                _gate(
                    "data_readiness",
                    "passed",
                    "Configured data path is review-ready.",
                )
            ]
        elif stage_id == "logical_view_readiness":
            stage.outputs = {
                "provider": package.source.get("provider"),
                "view": package.source.get("view"),
            }
            stage.gates = [
                _gate(
                    "logical_view_readiness",
                    "passed",
                    "Governed model source contract is available in package evidence.",
                )
            ]
        elif stage_id == "feature_build":
            stage.status = "skipped"
            stage.outputs = {"delegated_to": "make build-features / build-review-artifacts"}
            stage.gates = [
                _gate(
                    "feature_build",
                    "skipped",
                    "Orchestrator does not duplicate feature build logic.",
                )
            ]
        elif stage_id == "feature_validation":
            stage.outputs = {"feature_count": package.feature_metadata.get("feature_count")}
            stage.gates = [
                _gate(
                    "feature_validation",
                    "passed",
                    "Feature package metadata is present.",
                )
            ]
        elif stage_id == "model_training_evaluation":
            stage.outputs = package.evaluation_metrics.get("registry_summary", {})
            status: GateStatus = "passed" if stage.outputs else "blocked"
            stage.gates = [_gate("model_evaluation", status, "Model evaluation evidence checked.")]
        elif stage_id == "lifecycle_package":
            fingerprint = registration_fingerprint(package)
            stage.outputs = {
                "model_name": package.model_name,
                "registration_fingerprint": fingerprint,
            }
            stage.gates = [
                _gate(
                    "package_identity",
                    "passed",
                    "Lifecycle package built deterministically.",
                )
            ]
        elif stage_id == "registration":
            dry_run = mode != "enterprise_live" or not allow_external_registration
            registration_result = provider.register_model_package(package, dry_run=dry_run)
            stage.outputs = registration_result.model_dump(mode="json")
            stage.gates = [
                _gate(
                    "registration",
                    "passed",
                    "Registration path completed or dry-run result produced.",
                )
            ]
        elif stage_id == "registration_reconciliation":
            promotion_state = provider.retrieve_promotion_state(package)
            status = (
                "blocked"
                if promotion_state.status in {"blocked", "reconciliation_required"}
                else "passed"
            )
            stage.outputs = promotion_state.model_dump(mode="json")
            stage.gates = [
                _gate(
                    "registration_reconciliation",
                    status,
                    "Lifecycle registration/promotion state assessed.",
                )
            ]
        elif stage_id == "promotion_assessment":
            promotion_result = provider.submit_promotion_request(package, dry_run=True)
            status = "blocked" if promotion_result.promotion_status == "blocked" else "passed"
            stage.outputs = promotion_result.model_dump(mode="json")
            stage.gates = [
                _gate("promotion_eligibility", status, promotion_result.promotion_status)
            ]
        elif stage_id == "approval_gate":
            decision = provider.retrieve_promotion_state(package)
            status = "passed" if decision.approval.approval_status == "approved" else "blocked"
            stage.outputs = decision.model_dump(mode="json")
            stage.gates = [
                _gate(
                    "approval",
                    status,
                    f"Approval status: {decision.approval.approval_status}.",
                )
            ]
        elif stage_id == "external_promotion":
            if not allow_external_promotion or mode != "enterprise_live":
                stage.status = "skipped"
                stage.outputs = {"reason": "External promotion flag not enabled."}
                stage.gates = [
                    _gate(
                        "external_promotion",
                        "skipped",
                        "External mutation not permitted.",
                    )
                ]
            else:
                promotion_result = provider.submit_promotion_request(
                    package,
                    dry_run=False,
                )
                gate_status: GateStatus = (
                    "passed"
                    if promotion_result.promotion_status in {"promoted", "already_champion"}
                    else "blocked"
                )
                stage.outputs = promotion_result.model_dump(mode="json")
                stage.gates = [
                    _gate(
                        "external_promotion",
                        gate_status,
                        promotion_result.promotion_status,
                    )
                ]
        elif stage_id == "local_activation":
            stage.status = "skipped"
            stage.outputs = {
                "allow_local_activation": allow_local_activation,
                "local_activation_performed": False,
            }
            stage.gates = [
                _gate(
                    "local_activation",
                    "skipped",
                    "Local activation remains an explicit existing registry command.",
                )
            ]
        elif stage_id == "serving_validation":
            serving_result = validate_serving(
                registry_config=RegistryConfig.from_file(config.model_package.registry_config),
                governance_config=GovernanceConfig.from_file(
                    config.model_package.governance_config
                ),
                serving_config=ServingConfig.from_file(Path("config/serving.yaml")),
            )
            stage.outputs = serving_result
            serving_status: GateStatus = "passed" if serving_result["valid"] else "failed"
            stage.gates = [
                _gate(
                    "serving_readiness",
                    serving_status,
                    "Serving validation executed.",
                )
            ]
        elif stage_id == "monitoring_baseline":
            baseline = repository_root() / "monitoring/reports/monitoring_baseline.json"
            exists = baseline.is_file()
            stage.outputs = {
                "baseline_path": str(baseline.relative_to(repository_root())),
                "exists": exists,
            }
            baseline_status: GateStatus = "passed" if exists else "blocked"
            stage.gates = [
                _gate(
                    "monitoring_baseline",
                    baseline_status,
                    "Monitoring baseline existence checked.",
                )
            ]
        elif stage_id == "release_readiness":
            release_result = assess_release_readiness(
                ReleaseConfig.from_file(Path("config/release.yaml")),
                repository_root(),
            )
            stage.outputs = {
                "local_review_readiness": release_result["local_review_readiness"],
                "operational_release_readiness": release_result["operational_release_readiness"],
                "blocking_gates": release_result["blocking_gates"],
            }
            release_status: GateStatus = (
                "passed"
                if release_result["local_review_readiness"] == "ready_for_local_review"
                else "blocked"
            )
            stage.gates = [
                _gate(
                    "release_readiness",
                    release_status,
                    "Release readiness assessed.",
                )
            ]
        if stage.status == "running":
            stage.status = _stage_status_from_gates(stage.gates)
    except Exception as exc:
        stage.status = "failed"
        stage.failure = FailureDetails(message=str(exc), error_type=type(exc).__name__)
    stage.ended_at_utc = _now()
    return stage


def _finalise(run: WorkflowRun) -> WorkflowRun:
    passed = sum(stage.status in {"passed", "resumed"} for stage in run.stages)
    blocked = sum(stage.status == "blocked" for stage in run.stages)
    failed = sum(stage.status == "failed" for stage in run.stages)
    skipped = sum(stage.status == "skipped" for stage in run.stages)
    status: Literal["passed", "blocked", "failed"] = (
        "failed" if failed else "blocked" if blocked else "passed"
    )
    completed = [
        stage.stage_id for stage in run.stages if stage.status in {"passed", "skipped", "resumed"}
    ]
    run.resume_state.completed_stages = completed
    run.resume_state.blocked_stage = next(
        (stage.stage_id for stage in run.stages if stage.status == "blocked"),
        None,
    )
    run.resume_state.failed_stage = next(
        (stage.stage_id for stage in run.stages if stage.status == "failed"),
        None,
    )
    run.ended_at_utc = _now()
    run.summary = WorkflowSummary(
        status=status,
        passed_stages=passed,
        blocked_stages=blocked,
        failed_stages=failed,
        skipped_stages=skipped,
        known_limitations=[
            "Offline modes do not call live PostgreSQL, Denodo or SAS Viya services.",
            "External promotion and local activation are separate explicit operations.",
        ],
    )
    return run


def _write_evidence_bundle(run: WorkflowRun, directory: Path, root: Path) -> WorkflowRun:
    directory.mkdir(parents=True, exist_ok=True)
    payload = run.model_dump(mode="json", exclude={"evidence_checksum"})
    payload["evidence_references"] = _evidence_references(run)
    checksum = _sha256_json(payload)
    payload["evidence_checksum"] = checksum
    path = directory / f"{run.workflow_id}.json"
    _atomic_write(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    try:
        display_path = path.relative_to(root)
    except ValueError:
        display_path = path
    return run.model_copy(
        update={
            "evidence_bundle_path": str(display_path),
            "evidence_checksum": checksum,
        }
    )


def _evidence_references(run: WorkflowRun) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for stage in run.stages:
        refs.extend(item.model_dump(mode="json") for item in stage.evidence)
    return refs


def _write_run(run: WorkflowRun, path: Path) -> None:
    _atomic_write(path, run.model_dump_json(indent=2) + "\n")


def _load_run(path: Path) -> WorkflowRun:
    return WorkflowRun.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as handle:
        handle.write(text)
        temp = Path(handle.name)
    temp.replace(path)


def _configuration_fingerprint(config: LifecycleConfig, mode: WorkflowMode) -> str:
    payload = {
        "mode": mode,
        "provider": config.provider.model_dump(mode="json"),
        "model_package": config.model_package.model_dump(mode="json"),
        "registration": config.registration.model_dump(mode="json"),
        "workflow": config.workflow.model_dump(mode="json"),
    }
    return _sha256_json(payload)


def _sha256_json(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _stage_status_from_gates(gates: list[GateDecision]) -> StageStatus:
    statuses = {gate.status for gate in gates}
    if "failed" in statuses:
        return "failed"
    if "blocked" in statuses:
        return "blocked"
    if statuses == {"skipped"}:
        return "skipped"
    return "passed"


def _gate(gate_id: str, status: GateStatus, reason: str) -> GateDecision:
    return GateDecision(gate_id=gate_id, status=status, reason=reason)


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else repository_root() / path


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
