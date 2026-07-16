"""Typed configuration for deterministic synthetic data generation."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from ml_product.utils.paths import repository_root

OutputFormat = Literal["csv", "parquet"]
DatasetMode = Literal["sample", "full"]


class DatasetSettings(BaseModel):
    version: str
    mode: DatasetMode = "sample"
    seed: int
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self) -> DatasetSettings:
        if self.end_date < self.start_date:
            raise ValueError("dataset.end_date must be on or after dataset.start_date")
        return self


class CountSettings(BaseModel):
    patients: int = Field(gt=0)
    wards: int = Field(gt=0)


class AdmissionSettings(BaseModel):
    minimum_per_patient: int = Field(ge=0)
    maximum_per_patient: int = Field(ge=0)
    target_total: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_distribution(self) -> AdmissionSettings:
        if self.maximum_per_patient < self.minimum_per_patient:
            raise ValueError("admissions.maximum_per_patient must be >= minimum_per_patient")
        return self


class DiagnosisSettings(BaseModel):
    minimum_per_admission: int = Field(ge=1)
    maximum_per_admission: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_distribution(self) -> DiagnosisSettings:
        if self.maximum_per_admission < self.minimum_per_admission:
            raise ValueError("diagnoses.maximum_per_admission must be >= minimum_per_admission")
        return self


class OutputSettings(BaseModel):
    directory: Path
    formats: list[OutputFormat]
    overwrite: bool = False

    @field_validator("formats")
    @classmethod
    def validate_formats(cls, value: list[OutputFormat]) -> list[OutputFormat]:
        if not value:
            raise ValueError("outputs.formats must contain at least one format")
        return value


class QualityIssueSettings(BaseModel):
    enabled: bool = True
    rates: dict[str, float] = Field(default_factory=dict)

    @field_validator("rates")
    @classmethod
    def validate_rates(cls, value: dict[str, float]) -> dict[str, float]:
        for issue_type, rate in value.items():
            if rate < 0.0 or rate > 1.0:
                raise ValueError(f"quality issue rate out of range for {issue_type}: {rate}")
        return value


class SyntheticDataConfig(BaseModel):
    version: str
    description: str
    implementation_status: Literal["implemented"]
    enabled: bool
    dataset: DatasetSettings
    counts: CountSettings
    admissions: AdmissionSettings
    diagnoses: DiagnosisSettings
    outputs: OutputSettings
    quality_issues: QualityIssueSettings
    documentation: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_output_safety(self) -> SyntheticDataConfig:
        if self.dataset.mode == "full" and self.outputs.directory.as_posix() == "data/sample":
            raise ValueError("full generation mode must not target committed data/sample")
        return self

    @classmethod
    def from_file(cls, path: Path) -> SyntheticDataConfig:
        with path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)
        if not isinstance(raw, dict):
            raise ValueError(f"{path} must contain a YAML mapping")
        return cls.model_validate(raw)

    def fingerprint(self) -> str:
        payload = self.model_dump(mode="json", exclude={"outputs": {"directory"}})
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def output_directory(self) -> Path:
        path = self.outputs.directory
        if not path.is_absolute():
            path = repository_root() / path
        return path

    def with_overrides(
        self,
        *,
        mode: DatasetMode | None = None,
        output_dir: Path | None = None,
        seed: int | None = None,
        clean: bool = False,
        overwrite: bool | None = None,
    ) -> SyntheticDataConfig:
        data = self.model_dump()
        if mode is not None:
            data["dataset"]["mode"] = mode
        if output_dir is not None:
            data["outputs"]["directory"] = output_dir
        if seed is not None:
            data["dataset"]["seed"] = seed
        if clean:
            data["quality_issues"]["enabled"] = False
            data["quality_issues"]["rates"] = {}
        if overwrite is not None:
            data["outputs"]["overwrite"] = overwrite
        return SyntheticDataConfig.model_validate(data)
