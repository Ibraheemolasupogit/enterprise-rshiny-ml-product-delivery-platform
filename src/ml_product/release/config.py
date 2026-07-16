"""Typed Milestone 13 release configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ReleasePolicy(BaseModel):
    project_version_source: Literal["pyproject"]
    require_clean_validation: bool
    require_model_governance_consistency: bool
    require_registry_validation: bool
    require_reproducibility: bool
    require_security_checks: bool
    require_container_checks: bool


class ArtefactPolicy(BaseModel):
    api_image_name: str
    rshiny_image_name: str
    tag_strategy: Literal["semantic_version_and_commit"]
    publish_images: bool

    @field_validator("api_image_name", "rshiny_image_name")
    @classmethod
    def validate_image_name(cls, value: str) -> str:
        if not value or any(char in value for char in " /:@"):
            raise ValueError(
                "Image names must be local repository names without registry prefixes."
            )
        return value


class DeploymentPolicy(BaseModel):
    external_enabled: bool
    cloud_enabled: bool
    require_manual_approval: bool


class ModelReleasePolicy(BaseModel):
    require_approved_active_for_operational_release: bool
    permit_review_release: bool
    review_release_label: str = Field(min_length=1)


class ReleaseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    description: str
    implementation_status: Literal["implemented"]
    enabled: bool
    release: ReleasePolicy
    artefacts: ArtefactPolicy
    deployment: DeploymentPolicy
    model: ModelReleasePolicy

    @classmethod
    def from_file(cls, path: Path) -> ReleaseConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a YAML mapping.")
        return cls.model_validate(payload)

    @model_validator(mode="after")
    def validate_release_boundaries(self) -> ReleaseConfig:
        if self.artefacts.publish_images:
            raise ValueError("Milestone 13 must not publish container images.")
        if not self.enabled:
            raise ValueError("Release assurance configuration must be enabled.")
        if self.deployment.external_enabled or self.deployment.cloud_enabled:
            raise ValueError("Milestone 13 must not enable external or cloud deployment.")
        if not self.deployment.require_manual_approval:
            raise ValueError("Release approval must remain manual.")
        if not self.model.permit_review_release:
            raise ValueError("Local review release must be explicitly permitted.")
        if not self.model.require_approved_active_for_operational_release:
            raise ValueError("Operational release must require an approved active model.")
        return self
