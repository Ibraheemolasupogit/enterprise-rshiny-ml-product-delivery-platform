"""Typed serving configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ServiceConfig(BaseModel):
    host: str
    port: int
    environment: Literal["local", "staging", "production"]
    title: str
    api_version: str


class ModelServingConfig(BaseModel):
    source: Literal["registry"]
    require_active_model: bool
    allow_registered_candidate_for_local_review: bool


class PredictionConfig(BaseModel):
    probability_field: str
    threshold_source: Literal["registry"]
    include_risk_band: bool
    include_model_version: bool
    include_explanation_summary: bool


class LoggingConfig(BaseModel):
    log_predictions: bool
    log_input_values: bool
    log_identifiers: bool
    redact_sensitive_fields: bool
    event_log_path: Path

    @field_validator("event_log_path")
    @classmethod
    def reject_unsafe_path(cls, value: Path) -> Path:
        if value.is_absolute() or ".." in value.parts:
            raise ValueError("Prediction log path must be repository-relative.")
        return value


class SecurityConfig(BaseModel):
    authentication_mode: Literal["local_api_key"]
    api_key_environment_variable: str
    allow_unauthenticated_health: bool
    allow_unauthenticated_metadata: bool


class CorsConfig(BaseModel):
    enabled: bool
    allow_credentials: bool
    allowed_origins: list[str]

    @field_validator("allowed_origins")
    @classmethod
    def restrict_to_local_origins(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("At least one local CORS origin is required when configured.")
        for origin in value:
            if origin == "*" or not origin.startswith(("http://127.0.0.1:", "http://localhost:")):
                raise ValueError("CORS origins must be explicit local development origins.")
        return value

    @model_validator(mode="after")
    def reject_wildcard_credentials(self) -> CorsConfig:
        if self.allow_credentials:
            raise ValueError("CORS credentials are disabled for the local Shiny client.")
        return self


class LimitsConfig(BaseModel):
    maximum_batch_size: int = Field(gt=0, le=1000)
    request_timeout_seconds: int = Field(gt=0, le=120)


class RiskBandConfig(BaseModel):
    minimum: float = Field(ge=0.0, le=1.0)
    maximum: float = Field(ge=0.0, le=1.0)


class ServingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    description: str
    implementation_status: Literal["implemented"]
    enabled: bool
    service: ServiceConfig
    model: ModelServingConfig
    prediction: PredictionConfig
    logging: LoggingConfig
    security: SecurityConfig
    cors: CorsConfig
    limits: LimitsConfig
    risk_bands: dict[Literal["low", "medium", "high"], RiskBandConfig]

    @classmethod
    def from_file(cls, path: Path) -> ServingConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a YAML mapping.")
        return cls.model_validate(payload)

    @model_validator(mode="after")
    def validate_boundaries(self) -> ServingConfig:
        if self.model.allow_registered_candidate_for_local_review:
            raise ValueError("Review mode must be disabled by default in config.")
        ordered = [
            self.risk_bands["low"],
            self.risk_bands["medium"],
            self.risk_bands["high"],
        ]
        if ordered[0].minimum != 0.0 or ordered[-1].maximum != 1.0:
            raise ValueError("Risk bands must cover the full 0-1 range.")
        for left, right in zip(ordered, ordered[1:], strict=False):
            if left.maximum != right.minimum:
                raise ValueError("Risk bands must be contiguous without gaps or overlaps.")
        return self
