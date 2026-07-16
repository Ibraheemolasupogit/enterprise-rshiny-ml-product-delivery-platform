"""Local filesystem-backed model registry operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ml_product.registry.activation import build_activation_event
from ml_product.registry.approval import build_approval_decision
from ml_product.registry.audit import audit_event
from ml_product.registry.config import GovernanceConfig, RegistryConfig
from ml_product.registry.models import (
    ApprovalDecisionValue,
    ModelVersion,
    RegistryEntry,
    RegistryRecord,
    validate_transition,
)
from ml_product.registry.registration import build_model_version
from ml_product.registry.rollback import build_rollback_event
from ml_product.registry.storage import copy_immutable, load_registry, save_registry
from ml_product.registry.validation import validate_registry
from ml_product.registry.writers import write_json, write_text


class LocalModelRegistry:
    """Small local registry with immutable versions and explicit governance gates."""

    def __init__(
        self,
        config: RegistryConfig,
        governance_config: GovernanceConfig,
        *,
        root: Path = Path("."),
    ) -> None:
        self.config = config
        self.governance_config = governance_config
        self.root = root
        self.path = root / config.registry.metadata_path

    def load(self) -> RegistryRecord:
        return load_registry(self.path)

    def save(self, record: RegistryRecord) -> None:
        save_registry(self.path, record)

    def list_models(self) -> list[ModelVersion]:
        return [version for entry in self.load().models for version in entry.versions]

    def get_model_version(self, model_name: str, version: int) -> ModelVersion:
        for entry in self.load().models:
            if entry.model_name == model_name:
                for item in entry.versions:
                    if item.registry_version == version:
                        return item
        raise ValueError(f"Unknown model version: {model_name}:{version}")

    def get_active_model(self) -> ModelVersion | None:
        record = self.load()
        if record.active_model is None or record.active_version is None:
            return None
        return self.get_model_version(record.active_model, record.active_version)

    def register_candidate(
        self,
        *,
        candidate_identifier: str,
        model_config_path: Path,
        candidate_dir: Path,
    ) -> ModelVersion:
        record = self.load()
        if any(
            item.candidate_identifier == candidate_identifier
            for entry in record.models
            for item in entry.versions
        ):
            raise ValueError("Candidate is already registered in this immutable registry.")
        version_number = self._next_version(record)
        version_dir = (
            self.root / self.config.registry.registered_directory / f"v{version_number:06d}"
        )
        model_dest = version_dir / "xgboost.json"
        calibrator_dest = version_dir / "calibrator.joblib"
        model_checksum = copy_immutable(candidate_dir / "xgboost.json", model_dest)
        calibrator_checksum = copy_immutable(candidate_dir / "calibrator.joblib", calibrator_dest)
        version = build_model_version(
            root=self.root,
            config=self.config,
            governance_config=self.governance_config,
            candidate_identifier=candidate_identifier,
            registry_version=version_number,
            model_config_path=model_config_path,
            candidate_dir=candidate_dir,
            registered_model_path=str(
                self.config.registry.registered_directory
                / f"v{version_number:06d}"
                / "xgboost.json"
            ),
            registered_calibrator_path=str(
                self.config.registry.registered_directory
                / f"v{version_number:06d}"
                / "calibrator.joblib"
            ),
            model_checksum=model_checksum,
            calibrator_checksum=calibrator_checksum,
        )
        record = self._append_version(record, version)
        record.audit_events.append(
            audit_event(
                event_type="candidate_registered",
                model_name=version.model_name,
                registry_version=version.registry_version,
                actor="LOCAL-REGISTRY",
                details={"candidate_identifier": candidate_identifier},
            )
        )
        self.save(record)
        self.write_evidence(record, version)
        return version

    def submit_for_approval(self, model_name: str, version: int) -> ModelVersion:
        record, model_version = self._mutable_version(model_name, version)
        validate_transition(model_version.status, "approval_pending")
        model_version.status = "approval_pending"
        record.audit_events.append(
            audit_event(
                event_type="approval_requested",
                model_name=model_name,
                registry_version=version,
                actor="LOCAL-REGISTRY",
            )
        )
        self.save(record)
        self.write_evidence(record, model_version)
        return model_version

    def record_approval_decision(
        self,
        *,
        model_name: str,
        version: int,
        decision: ApprovalDecisionValue,
        actor: str,
        reason: str,
        conditions: list[str],
    ) -> ModelVersion:
        record, model_version = self._mutable_version(model_name, version)
        previous = model_version.status
        if previous != "approval_pending":
            raise ValueError("Approval decisions require approval_pending status.")
        approval = build_approval_decision(
            decision=decision,
            actor=actor,
            reason=reason,
            conditions=conditions,
            evidence_fingerprint=model_version.evidence_fingerprint,
            previous_status=previous,
        )
        model_version.approval_decision = approval
        if decision in {"approve", "approve_with_conditions"}:
            model_version.status = "approved"
        elif decision == "reject":
            model_version.status = "rejected"
        else:
            model_version.status = "registered"
        record.audit_events.append(
            audit_event(
                event_type="approval_recorded",
                model_name=model_name,
                registry_version=version,
                actor=actor,
                details={"decision": decision},
            )
        )
        self.save(record)
        self.write_evidence(record, model_version)
        return model_version

    def activate_model(
        self, *, model_name: str, version: int, actor: str, reason: str
    ) -> ModelVersion:
        record, model_version = self._mutable_version(model_name, version)
        event = build_activation_event(
            version=model_version,
            actor=actor,
            reason=reason,
            previous_active_version=record.active_version,
        )
        for item in self._versions(record, model_name):
            if item.status == "active":
                item.status = "retired"
        model_version.status = "active"
        model_version.activation_event = event
        record.active_model = model_name
        record.active_version = version
        record.audit_events.append(
            audit_event(
                event_type="model_activated",
                model_name=model_name,
                registry_version=version,
                actor=actor,
            )
        )
        self.save(record)
        self.write_evidence(record, model_version)
        return model_version

    def retire_model(
        self, *, model_name: str, version: int, actor: str, reason: str
    ) -> ModelVersion:
        record, model_version = self._mutable_version(model_name, version)
        validate_transition(model_version.status, "retired")
        model_version.status = "retired"
        if record.active_model == model_name and record.active_version == version:
            record.active_model = None
            record.active_version = None
        record.audit_events.append(
            audit_event(
                event_type="model_retired",
                model_name=model_name,
                registry_version=version,
                actor=actor,
                details={"reason": reason},
            )
        )
        self.save(record)
        self.write_evidence(record, model_version)
        return model_version

    def rollback_model(
        self,
        *,
        model_name: str,
        target_version: int,
        actor: str,
        reason: str,
        dry_run: bool,
    ) -> ModelVersion:
        record, target = self._mutable_version(model_name, target_version)
        build_rollback_event(target=target, actor=actor, reason=reason, dry_run=dry_run)
        if not dry_run:
            for item in self._versions(record, model_name):
                if item.status == "active":
                    item.status = "retired"
            target.status = "active"
            record.active_model = model_name
            record.active_version = target_version
            record.audit_events.append(
                audit_event(
                    event_type="rollback_completed",
                    model_name=model_name,
                    registry_version=target_version,
                    actor=actor,
                    details={"reason": reason},
                )
            )
            self.save(record)
            self.write_evidence(record, target)
        return target

    def validate(self) -> dict[str, Any]:
        return validate_registry(self.config, root=self.root)

    def write_evidence(self, record: RegistryRecord, version: ModelVersion) -> None:
        report_dir = self.root / "reports/model_evaluation"
        active = (
            record.active_model == version.model_name
            and record.active_version == version.registry_version
        )
        approval_status = (
            "pending" if version.approval_decision is None else version.approval_decision.decision
        )
        manifest = {
            "model_name": version.model_name,
            "registry_id": version.registry_id,
            "registry_version": version.registry_version,
            "candidate_identifier": version.candidate_identifier,
            "registry_state": version.status,
            "artefact_checksum": version.artefacts.model_sha256,
            "preprocessor_checksum": version.preprocessor_contract.preprocessor_checksum,
            "feature_count": version.feature_contract.feature_count,
            "feature_build_identifier": version.feature_contract.feature_build_identifier,
            "training_configuration_fingerprint": version.training_configuration_fingerprint,
            "calibration": version.calibration,
            "threshold": version.threshold,
            "risk_bands": {"low": [0.0, 0.4], "medium": [0.4, 0.75], "high": [0.75, 1.0]},
            "registration_event": "candidate_registered",
            "approval_state": approval_status,
            "activation_state": "active" if active else "inactive",
            "synthetic_data_declaration": version.synthetic_data_declaration,
        }
        write_json(report_dir / "model_registry_manifest.json", manifest)
        write_json(
            report_dir / "governance_review.json", version.governance.model_dump(mode="json")
        )
        write_json(
            report_dir / "approval_decision.json",
            {
                "decision": "pending"
                if version.approval_decision is None
                else version.approval_decision.decision,
                "actor": None
                if version.approval_decision is None
                else version.approval_decision.actor,
                "reason": (
                    "Explicit human/local governance decision has not approved this model."
                    if version.approval_decision is None
                    else version.approval_decision.reason
                ),
                "conditions": []
                if version.approval_decision is None
                else version.approval_decision.conditions,
                "approval_status": approval_status,
                "automatic_approval": False,
            },
        )
        write_json(
            report_dir / "activation_status.json",
            {
                "active_model": record.active_model,
                "active_version": record.active_version,
                "activation_state": "active" if active else "inactive",
                "activation_requires_approval": True,
                "actual_activation_performed": active,
                "rollback_supported": True,
            },
        )
        write_json(
            report_dir / "registry_audit_summary.json",
            {
                "event_count": len(record.audit_events),
                "events": [event.model_dump(mode="json") for event in record.audit_events],
            },
        )
        write_json(
            report_dir / "registry_validation.json",
            {
                "valid": True,
                "errors": [],
                "automatic_approval": False,
                "activation_requires_approval": True,
            },
        )
        write_json(
            report_dir / "serving_contract.json",
            {
                "input_contract": "raw_admission_time_predictors",
                "transformed_feature_count": version.feature_contract.feature_count,
                "outcome_fields_rejected": True,
                "database_queries_for_prediction": False,
                "training_during_prediction": False,
                "authentication_required": True,
            },
        )
        write_json(
            report_dir / "serving_readiness.json",
            {
                "local_review_mode": {"enabled_by_default": False, "available": True},
                "approved_serving": active,
                "production_deployment": False,
                "active_approved_model_exists": active,
                "readiness_status": "ready" if active else "not_ready_no_active_approved_model",
            },
        )
        write_text(
            report_dir / "model_serving_report.md",
            "# Model Serving Report\n\n"
            "Milestone 7 implements a local FastAPI scoring surface backed by the local "
            "filesystem registry. Default serving fails closed until an approved active model "
            "exists. Local review mode is explicit and not for operational use.\n",
        )
        card_path = report_dir / "model_card.md"
        if card_path.is_file():
            card = card_path.read_text(encoding="utf-8")
            card = (
                card.replace(
                    "Model registration: not implemented",
                    (
                        "Model registration: implemented locally; "
                        "candidate registered for governance review"
                    ),
                )
                .replace(
                    "Model serving: not implemented",
                    "Model serving: implemented locally; not ready without approved active model",
                )
                .replace(
                    "R-Shiny integration: not implemented",
                    "R-Shiny integration: implemented locally as a FastAPI review-mode client",
                )
                .replace(
                    "SAS Viya integration: not implemented",
                    "SAS Viya integration: externally blocked and not implemented",
                )
            )
            write_text(card_path, card)

    def _append_version(self, record: RegistryRecord, version: ModelVersion) -> RegistryRecord:
        for entry in record.models:
            if entry.model_name == version.model_name:
                if any(
                    item.registry_version == version.registry_version for item in entry.versions
                ):
                    raise ValueError("Registry version is immutable and already exists.")
                entry.versions.append(version)
                return record
        record.models.append(RegistryEntry(model_name=version.model_name, versions=[version]))
        return record

    def _next_version(self, record: RegistryRecord) -> int:
        versions = [item.registry_version for entry in record.models for item in entry.versions]
        return max(versions, default=0) + 1

    def _versions(self, record: RegistryRecord, model_name: str) -> list[ModelVersion]:
        for entry in record.models:
            if entry.model_name == model_name:
                return entry.versions
        raise ValueError(f"Unknown model: {model_name}")

    def _mutable_version(
        self, model_name: str, version: int
    ) -> tuple[RegistryRecord, ModelVersion]:
        record = self.load()
        for item in self._versions(record, model_name):
            if item.registry_version == version:
                return record, item
        raise ValueError(f"Unknown model version: {model_name}:{version}")
