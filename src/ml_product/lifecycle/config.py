"""Configuration for provider-neutral model lifecycle integrations."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

ProviderName = Literal["local", "sas_viya"]
AuthenticationMode = Literal["none", "bearer_token", "client_credentials"]


class ProviderSelection(BaseModel):
    selected: ProviderName = "local"
    enabled: bool = True


class LocalLifecycleConfig(BaseModel):
    provider_label: Literal["local_model_lifecycle"] = "local_model_lifecycle"
    registry_config: Path = Path("config/model_registry.yaml")
    governance_config: Path = Path("config/model_governance.yaml")


class SasViyaConfig(BaseModel):
    enabled: bool = False
    provider_label: Literal["real_sas_viya"] = "real_sas_viya"
    base_url: str
    authentication_mode: AuthenticationMode = "bearer_token"
    project_identifier: str
    model_repository_identifier: str
    model_name: str
    readiness_path: str = "/SASLogon/actuator/health"
    timeout_seconds: int = Field(default=10, gt=0, le=120)
    verify_tls: bool = True
    client_id_env: str = "SAS_VIYA_CLIENT_ID"
    client_secret_env: str = "SAS_VIYA_CLIENT_SECRET"
    access_token_env: str = "SAS_VIYA_ACCESS_TOKEN"

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        if not value.startswith(("https://", "http://")):
            raise ValueError("SAS Viya base_url must include http:// or https://")
        return value.rstrip("/")

    @field_validator("readiness_path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("SAS Viya readiness_path must start with /")
        return value


class ModelPackageConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    output_path: Path = Path("reports/model_evaluation/model_lifecycle_package.json")
    model_config_path: Path = Field(
        default=Path("config/model_training.yaml"),
        alias="model_config",
    )
    registry_config: Path = Path("config/model_registry.yaml")
    governance_config: Path = Path("config/model_governance.yaml")
    model_name: str
    registry_version: int = Field(gt=0)
    report_directory: Path = Path("reports/model_evaluation")


class LifecycleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    description: str
    implementation_status: Literal["implemented"]
    enabled: bool
    provider: ProviderSelection
    local: LocalLifecycleConfig
    sas_viya: SasViyaConfig
    model_package: ModelPackageConfig

    @classmethod
    def from_file(cls, path: Path) -> LifecycleConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a YAML mapping.")
        return cls.model_validate(payload)
