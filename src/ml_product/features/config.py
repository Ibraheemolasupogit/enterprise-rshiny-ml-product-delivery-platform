"""Configuration models for admission-time feature engineering."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from ml_product.utils.paths import repository_root


class SourceConfig(BaseModel):
    provider: Literal["denodo_compatible_local"]
    view: Literal["curated.model_source_view"]
    database_config: Path = Path("config/database.yaml")


class PredictionContractConfig(BaseModel):
    prediction_point: str
    unit_of_analysis: Literal["admission"]
    target_column: Literal["long_stay_flag_governed"]
    positive_class: bool
    target_definition: str


class EligibilityConfig(BaseModel):
    flag_column: str
    exclusion_reason_column: str
    require_operational_context: bool = False


class FeatureGroups(BaseModel):
    numeric: list[str] = Field(default_factory=list)
    categorical: list[str] = Field(default_factory=list)
    boolean: list[str] = Field(default_factory=list)
    temporal_derivations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_features(self) -> FeatureGroups:
        all_features = [*self.numeric, *self.categorical, *self.boolean]
        duplicates = sorted(
            {feature for feature in all_features if all_features.count(feature) > 1}
        )
        if duplicates:
            raise ValueError(f"Duplicate configured features: {duplicates}")
        return self

    @property
    def predictors(self) -> list[str]:
        return [*self.numeric, *self.categorical, *self.boolean]


class MissingnessConfig(BaseModel):
    numeric: Literal["median"]
    categorical: Literal["explicit_missing_category"]
    boolean: Literal["mode"]
    add_missing_indicators: bool = True


class EncodingConfig(BaseModel):
    categorical: Literal["one_hot"]
    handle_unknown: Literal["ignore"]


class ScalingConfig(BaseModel):
    numeric: Literal["standard"]


class SplittingConfig(BaseModel):
    strategy: Literal["temporal"]
    train_fraction: float
    validation_fraction: float
    test_fraction: float
    group_by_patient: bool
    seed: int

    @model_validator(mode="after")
    def validate_fractions(self) -> SplittingConfig:
        total = self.train_fraction + self.validation_fraction + self.test_fraction
        if abs(total - 1.0) > 0.000001:
            raise ValueError("Split fractions must sum to one.")
        for name, value in (
            ("train_fraction", self.train_fraction),
            ("validation_fraction", self.validation_fraction),
            ("test_fraction", self.test_fraction),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be positive.")
        return self


class OutputConfig(BaseModel):
    directory: Path
    evidence_directory: Path
    formats: list[Literal["parquet", "csv"]]

    @field_validator("formats")
    @classmethod
    def validate_formats(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("At least one output format is required.")
        return value


class FeatureConfig(BaseModel):
    version: str
    description: str
    implementation_status: Literal["implemented"]
    enabled: bool
    source: SourceConfig
    prediction_contract: PredictionContractConfig
    identifiers: list[str]
    eligibility: EligibilityConfig
    features: FeatureGroups
    excluded_predictors: list[str]
    missingness: MissingnessConfig
    encoding: EncodingConfig
    scaling: ScalingConfig
    splitting: SplittingConfig
    outputs: OutputConfig

    @classmethod
    def from_file(cls, path: Path = Path("config/features.yaml")) -> FeatureConfig:
        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)
        if not isinstance(payload, dict):
            raise ValueError("Feature configuration must contain a YAML mapping.")
        return cls.model_validate(payload)

    @model_validator(mode="after")
    def validate_predictor_boundaries(self) -> FeatureConfig:
        predictors = self.features.predictors
        blocked = set(self.excluded_predictors) | set(self.identifiers)
        if self.prediction_contract.target_column in predictors:
            raise ValueError("Target column cannot be configured as a predictor.")
        prohibited = sorted(blocked.intersection(predictors))
        if prohibited:
            raise ValueError(f"Prohibited predictors configured: {prohibited}")
        if self.identifiers != ["admission_id", "patient_id"]:
            raise ValueError("Milestone 5 identifiers must be admission_id and patient_id.")
        return self

    def resolved_output_directory(self, override: Path | None = None) -> Path:
        return _resolve_safe_path(override or self.outputs.directory)

    def resolved_evidence_directory(self) -> Path:
        return _resolve_safe_path(self.outputs.evidence_directory)

    def resolved_database_config(self, override: Path | None = None) -> Path:
        return _resolve_safe_path(override or self.source.database_config, must_be_under_root=True)


def _resolve_safe_path(path: Path, *, must_be_under_root: bool = True) -> Path:
    root = repository_root().resolve()
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve()
    if must_be_under_root and not resolved.is_relative_to(root):
        tmp_root = Path(tempfile.gettempdir()).resolve()
        private_tmp = Path("/private/tmp").resolve()
        if not resolved.is_relative_to(tmp_root) and not resolved.is_relative_to(private_tmp):
            raise ValueError(f"Unsafe path outside repository root or temporary directory: {path}")
    return resolved
