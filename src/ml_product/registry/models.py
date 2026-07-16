"""Registry record models and state transition rules."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

RegistryState = Literal[
    "candidate",
    "registered",
    "approval_pending",
    "approved",
    "active",
    "rejected",
    "retired",
    "archived",
]
ApprovalDecisionValue = Literal["approve", "approve_with_conditions", "reject", "defer"]

VALID_TRANSITIONS: dict[str, set[str]] = {
    "candidate": {"registered"},
    "registered": {"approval_pending"},
    "approval_pending": {"approved", "rejected", "registered"},
    "approved": {"active", "retired"},
    "active": {"retired"},
    "rejected": {"archived"},
    "retired": {"archived", "active"},
    "archived": set(),
}


class ArtefactReference(BaseModel):
    model_path: str
    calibrator_path: str
    model_sha256: str
    calibrator_sha256: str


class FeatureContract(BaseModel):
    feature_count: int
    feature_names: list[str]
    feature_schema_fingerprint: str
    feature_build_identifier: str


class PreprocessorContract(BaseModel):
    preprocessor_fingerprint: str
    preprocessor_checksum: str
    source_path: str


class EvaluationSummary(BaseModel):
    validation_pr_auc: float
    validation_brier_score: float
    validation_recall: float
    validation_precision: float
    test_pr_auc: float
    test_roc_auc: float
    test_brier_score: float
    test_recall: float
    test_specificity: float
    test_balanced_accuracy: float
    test_set_used_for_selection: bool


class GovernanceAssessment(BaseModel):
    recommended_decision: ApprovalDecisionValue
    hard_requirements: dict[str, bool]
    review_flags: list[dict[str, str]]
    conditions: list[str]
    informational_limitations: list[str]
    human_decision_required: bool = True


class ApprovalDecision(BaseModel):
    decision: ApprovalDecisionValue
    actor: str
    reason: str
    conditions: list[str] = Field(default_factory=list)
    evidence_fingerprint: str
    decided_at_utc: str
    previous_status: RegistryState

    @field_validator("actor", "reason")
    @classmethod
    def require_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Actor and reason are required.")
        return value

    @model_validator(mode="after")
    def validate_conditions(self) -> ApprovalDecision:
        if self.decision == "approve_with_conditions" and not self.conditions:
            raise ValueError("Conditional approval requires conditions.")
        return self


class ActivationEvent(BaseModel):
    actor: str
    activated_at_utc: str
    previous_active_version: int | None
    reason: str


class RollbackEvent(BaseModel):
    actor: str
    target_version: int
    rolled_back_at_utc: str
    reason: str
    dry_run: bool


class AuditEvent(BaseModel):
    event_type: str
    model_name: str
    registry_version: int
    timestamp_utc: str
    actor: str
    details: dict[str, str]


class ModelVersion(BaseModel):
    model_name: str
    registry_id: str
    registry_version: int
    status: RegistryState
    model_family: str
    candidate_identifier: str
    calibration: str
    threshold: float
    artefacts: ArtefactReference
    feature_contract: FeatureContract
    preprocessor_contract: PreprocessorContract
    evaluation_summary: EvaluationSummary
    governance: GovernanceAssessment
    approval_decision: ApprovalDecision | None = None
    activation_event: ActivationEvent | None = None
    created_at_utc: str
    training_configuration_fingerprint: str
    evidence_fingerprint: str
    synthetic_data_declaration: str


class RegistryEntry(BaseModel):
    model_name: str
    versions: list[ModelVersion] = Field(default_factory=list)


class RegistryRecord(BaseModel):
    version: int
    registry_type: Literal["local_filesystem"]
    active_model: str | None = None
    active_version: int | None = None
    models: list[RegistryEntry] = Field(default_factory=list)
    audit_events: list[AuditEvent] = Field(default_factory=list)


def validate_transition(current: str, target: str) -> None:
    if target not in VALID_TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid registry transition: {current} -> {target}.")
