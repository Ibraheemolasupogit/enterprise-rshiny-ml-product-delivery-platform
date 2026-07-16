"""Typed database configuration for Milestone 3."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator

from ml_product.utils.paths import repository_root


class EngineConfig(BaseModel):
    type: Literal["duckdb"]
    database_path: Path
    read_only: bool = False


class SourceConfig(BaseModel):
    directory: Path
    preferred_format: Literal["parquet", "csv"] = "parquet"
    fallback_format: Literal["csv"] = "csv"


class SchemaConfig(BaseModel):
    raw: str = "raw"
    staged: str = "staged"
    curated: str = "curated"
    quality: str = "quality"
    metadata: str = "metadata"


class LoadingConfig(BaseModel):
    replace_existing: bool = True
    validate_checksums: bool = True
    validate_manifest: bool = True
    preserve_source_rows: bool = True


class QualityConfig(BaseModel):
    reconcile_intentional_issues: bool = True
    fail_on_unexpected_issues: bool = True
    quarantine_invalid_records: bool = True


class LogicalLayerConfig(BaseModel):
    provider: Literal["denodo_compatible_local"]
    adapter: Literal["duckdb"]
    default_limit: int = Field(default=100, gt=0)
    max_limit: int = Field(default=1000, gt=0)
    allow_arbitrary_sql: bool = False

    @model_validator(mode="after")
    def validate_limits(self) -> LogicalLayerConfig:
        if self.default_limit > self.max_limit:
            raise ValueError("logical_layer.default_limit must be <= max_limit")
        return self


class DatabaseConfig(BaseModel):
    version: str
    description: str
    implementation_status: Literal["implemented"]
    enabled: bool
    engine: EngineConfig
    sources: SourceConfig
    schemas: SchemaConfig
    loading: LoadingConfig
    quality: QualityConfig
    logical_layer: LogicalLayerConfig

    @classmethod
    def from_file(cls, path: Path) -> DatabaseConfig:
        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a YAML mapping")
        return cls.model_validate(payload)

    def database_path(self) -> Path:
        path = self.engine.database_path
        return path if path.is_absolute() else repository_root() / path

    def source_directory(self) -> Path:
        path = self.sources.directory
        return path if path.is_absolute() else repository_root() / path

    def with_overrides(
        self,
        *,
        source_dir: Path | None = None,
        database_path: Path | None = None,
        replace: bool | None = None,
        preferred_format: Literal["parquet", "csv"] | None = None,
    ) -> DatabaseConfig:
        data = self.model_dump()
        if source_dir is not None:
            data["sources"]["directory"] = source_dir
        if database_path is not None:
            data["engine"]["database_path"] = database_path
        if replace is not None:
            data["loading"]["replace_existing"] = replace
        if preferred_format is not None:
            data["sources"]["preferred_format"] = preferred_format
        return DatabaseConfig.model_validate(data)
