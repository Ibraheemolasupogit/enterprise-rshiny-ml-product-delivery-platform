"""Typed lifecycle registration domain models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RegistrationStatus = Literal["registered", "already_registered", "reconciled", "failed"]
MetadataSyncStatus = Literal["not_attempted", "synchronised", "mismatch", "failed"]
ReconciliationStatus = Literal["matched", "mismatch", "missing_external", "unsupported"]
PromotionStatus = Literal[
    "eligible",
    "blocked",
    "pending_approval",
    "approved",
    "rejected",
    "promoted",
    "already_champion",
    "reconciliation_required",
    "failed",
]
LifecycleState = Literal["registered", "approval_pending", "approved", "promoted", "active"]


class ReconciliationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ReconciliationStatus
    matched_fields: dict[str, Any] = Field(default_factory=dict)
    mismatches: dict[str, dict[str, Any]] = Field(default_factory=dict)
    missing_external_fields: list[str] = Field(default_factory=list)
    unsupported_fields: list[str] = Field(default_factory=list)


class RegistrationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    registration_status: RegistrationStatus
    local_model_id: str
    local_model_version: int
    local_build_identifier: str
    external_project_id: str | None
    external_model_id: str | None
    external_model_version_id: str | None
    registration_fingerprint: str
    registered_timestamp_utc: str
    metadata_synchronisation_status: MetadataSyncStatus
    warnings: list[str] = Field(default_factory=list)
    evidence_path: str | None = None
    reconciliation: ReconciliationResult | None = None


class LinkageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    local_model_id: str
    local_model_version: int
    local_build_identifier: str
    registration_fingerprint: str
    external_project_id: str | None
    external_model_id: str | None
    external_model_version_id: str | None
    metadata_sync_status: MetadataSyncStatus
    first_registered_at_utc: str
    last_reconciled_at_utc: str
    evidence_path: str | None = None
    evidence_checksum: str | None = None


class LinkageStorePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "lifecycle-linkage/v1"
    records: list[LinkageRecord] = Field(default_factory=list)


class ChampionReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model_name: str
    local_model_id: str | None = None
    local_model_version: int | None = None
    external_model_id: str | None = None
    external_model_version_id: str | None = None
    registration_fingerprint: str | None = None
    lifecycle_state: str


class ChallengerReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model_name: str
    local_model_id: str
    local_model_version: int
    local_build_identifier: str
    external_model_id: str | None = None
    external_model_version_id: str | None = None
    registration_fingerprint: str
    lifecycle_state: str


class ApprovalEvidenceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_status: Literal["missing", "pending", "approved", "rejected"]
    actor: str | None = None
    decided_at_utc: str | None = None
    evidence_fingerprint: str | None = None
    reason: str | None = None


class LifecycleStatusTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model_name: str
    model_version: int
    previous_state: str | None
    target_state: str
    accepted: bool
    reason: str


class ChampionChallengerComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    champion: ChampionReference | None
    challenger: ChallengerReference
    model_family: str
    dataset_version: str | None
    source_fingerprint: str | None
    key_evaluation_metrics: dict[str, Any]
    threshold_summary: dict[str, Any]
    calibration_summary: dict[str, Any]
    fairness_summary: dict[str, Any]
    governance_status: dict[str, Any]
    approval: ApprovalEvidenceReference
    compatibility_status: Literal["compatible", "unknown", "incompatible"]
    promotion_eligibility: PromotionStatus
    blocking_reasons: list[str] = Field(default_factory=list)


class PromotionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model_name: str
    local_model_id: str
    local_model_version: int
    external_model_id: str | None
    external_model_version_id: str | None
    registration_fingerprint: str
    requested_by: str
    reason: str
    dry_run: bool = False


class PromotionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: PromotionStatus
    eligible: bool
    blocking_reasons: list[str] = Field(default_factory=list)
    approval: ApprovalEvidenceReference


class ExternalLifecycleReconciliation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["aligned", "divergent", "missing_external", "reconciliation_required"]
    local_active_version: int | None
    external_champion_version_id: str | None
    details: dict[str, Any] = Field(default_factory=dict)


class PromotionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    promotion_status: PromotionStatus
    local_model_id: str
    local_model_version: int
    external_model_id: str | None
    external_model_version_id: str | None
    registration_fingerprint: str
    champion_before: ChampionReference | None
    champion_after: ChampionReference | None
    approval: ApprovalEvidenceReference
    blocking_reasons: list[str] = Field(default_factory=list)
    evidence_path: str | None = None
    evidence_checksum: str | None = None
    local_activation_performed: bool = False
    reconciliation: ExternalLifecycleReconciliation | None = None
