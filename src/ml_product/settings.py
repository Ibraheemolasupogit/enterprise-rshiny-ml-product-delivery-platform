"""Typed settings and YAML configuration loading for Milestone 1."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from ml_product.utils.paths import repository_root

IntegrationMode = Literal[
    "not_implemented",
    "real_denodo",
    "denodo_compatible_local",
    "real_sas_viya",
    "local_model_lifecycle",
]


class AppSettings(BaseSettings):
    """Environment-driven settings used by validation and future services."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(default="sqlite:///local-placeholder.db", alias="DATABASE_URL")
    model_api_host: str = Field(default="127.0.0.1", alias="MODEL_API_HOST")
    model_api_port: int = Field(default=8000, alias="MODEL_API_PORT")
    shiny_host: str = Field(default="127.0.0.1", alias="SHINY_HOST")
    shiny_port: int = Field(default=3838, alias="SHINY_PORT")
    model_registry_path: str = Field(default="models", alias="MODEL_REGISTRY_PATH")
    feedback_database_url: str = Field(
        default="sqlite:///feedback-placeholder.db", alias="FEEDBACK_DATABASE_URL"
    )
    denodo_integration_mode: IntegrationMode = Field(
        default="denodo_compatible_local", alias="DENODO_INTEGRATION_MODE"
    )
    sas_viya_integration_mode: IntegrationMode = Field(
        default="local_model_lifecycle", alias="SAS_VIYA_INTEGRATION_MODE"
    )


class ConfigDocument(BaseModel):
    """Common fields required in Milestone 1 YAML configuration files."""

    version: str
    description: str
    implementation_status: Literal["implemented", "planned", "documented_target"]
    enabled: bool


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML document and ensure it is a mapping."""

    with path.open("r", encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    if not isinstance(document, dict):
        raise ValueError(f"{path} must contain a YAML mapping.")
    return document


def load_config_document(path: Path) -> ConfigDocument:
    """Load and validate common Milestone 1 config metadata."""

    try:
        return ConfigDocument.model_validate(load_yaml(path))
    except ValidationError as exc:
        raise ValueError(f"{path} failed config validation: {exc}") from exc


def config_path(*parts: str) -> Path:
    """Resolve a path below the repository config directory."""

    return repository_root() / "config" / Path(*parts)


def load_settings() -> AppSettings:
    """Return typed application settings from environment variables."""

    return AppSettings()
