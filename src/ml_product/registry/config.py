"""Typed configuration for local registry and governance gates."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RegistryPaths(BaseModel):
    type: Literal["local_filesystem"]
    metadata_path: Path
    registered_directory: Path
    approved_directory: Path
    archived_directory: Path

    @field_validator(
        "metadata_path", "registered_directory", "approved_directory", "archived_directory"
    )
    @classmethod
    def reject_unsafe_paths(cls, value: Path) -> Path:
        text = str(value)
        if value.is_absolute() or ".." in value.parts or text.startswith("~"):
            raise ValueError("Registry paths must be repository-relative safe paths.")
        return value


class RegistrationPolicy(BaseModel):
    require_candidate_recommendation: bool
    require_reproducibility_pass: bool
    require_feature_schema_match: bool
    require_test_set_lock: bool
    copy_artifact: bool


class ApprovalPolicy(BaseModel):
    automatic_approval: bool
    require_human_decision: bool
    allowed_decisions: list[Literal["approve", "approve_with_conditions", "reject", "defer"]]
    required_evidence: list[str]

    @model_validator(mode="after")
    def validate_approval(self) -> ApprovalPolicy:
        if self.automatic_approval:
            raise ValueError("Automatic approval must remain disabled.")
        if not self.require_human_decision:
            raise ValueError("Human decision must be required.")
        return self


class ActivationPolicy(BaseModel):
    require_approved_status: bool
    allow_single_active_model: bool
    enable_rollback: bool

    @model_validator(mode="after")
    def validate_activation(self) -> ActivationPolicy:
        if not self.require_approved_status:
            raise ValueError("Activation must require approved status.")
        return self


class RegistryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    description: str
    implementation_status: Literal["implemented"]
    enabled: bool
    registry: RegistryPaths
    registration: RegistrationPolicy
    approval: ApprovalPolicy
    activation: ActivationPolicy

    @classmethod
    def from_file(cls, path: Path) -> RegistryConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a YAML mapping.")
        return cls.model_validate(payload)


class MinimumRequirements(BaseModel):
    reproducibility_passed: bool
    test_set_used_for_selection: bool
    leakage_violations: int
    feature_schema_match: bool
    model_card_complete: bool
    explainability_available: bool
    fairness_report_available: bool


class ReviewFlags(BaseModel):
    minimum_test_specificity: float = Field(ge=0.0, le=1.0)
    maximum_validation_test_pr_auc_drop: float = Field(ge=0.0, le=1.0)
    minimum_test_balanced_accuracy: float = Field(ge=0.0, le=1.0)
    minimum_test_recall: float = Field(ge=0.0, le=1.0)


class DecisionPolicy(BaseModel):
    hard_failures: list[str]
    conditional_flags: list[str]


class GovernanceApproval(BaseModel):
    automatic: bool

    @field_validator("automatic")
    @classmethod
    def reject_automatic(cls, value: bool) -> bool:
        if value:
            raise ValueError("Governance approval cannot be automatic.")
        return value


class GovernanceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    description: str
    implementation_status: Literal["implemented"]
    enabled: bool
    approval: GovernanceApproval
    minimum_requirements: MinimumRequirements
    review_flags: ReviewFlags
    decision_policy: DecisionPolicy

    @classmethod
    def from_file(cls, path: Path) -> GovernanceConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a YAML mapping.")
        return cls.model_validate(payload)
