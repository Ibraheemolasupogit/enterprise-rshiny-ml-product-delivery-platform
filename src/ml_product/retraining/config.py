"""Typed configuration for controlled retraining."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class WorkflowConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    automatic_execution: bool
    require_monitoring_review: bool
    require_human_initiation: bool
    require_labels: bool

    @model_validator(mode="after")
    def _safe_workflow(self) -> WorkflowConfig:
        if self.automatic_execution:
            raise ValueError("Milestone 12 retraining must not execute automatically.")
        if not self.require_human_initiation:
            raise ValueError("Retraining must require human initiation.")
        if not self.require_labels:
            raise ValueError("Retraining must require labels.")
        return self


class EligibilityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed_monitoring_dispositions: list[str]
    minimum_labelled_rows: int
    minimum_positive_rows: int
    minimum_negative_rows: int
    require_valid_schema: bool
    require_feature_contract_match: bool
    fail_on_unexpected_quality_issues: bool

    @field_validator("minimum_labelled_rows", "minimum_positive_rows", "minimum_negative_rows")
    @classmethod
    def _positive_counts(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Retraining eligibility counts must be positive.")
        return value


class DatasetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: Literal["governed_labelled_monitoring_window"]
    prediction_point: Literal["admission"]
    target_column: str
    preserve_patient_grouping: bool
    temporal_split: bool
    train_fraction: float
    validation_fraction: float
    random_seed: int

    @model_validator(mode="after")
    def _valid_split(self) -> DatasetConfig:
        total = self.train_fraction + self.validation_fraction
        if abs(total - 1.0) > 1e-9:
            raise ValueError("Retraining train and validation fractions must sum to 1.")
        if not 0 < self.train_fraction < 1 or not 0 < self.validation_fraction < 1:
            raise ValueError("Retraining split fractions must be between 0 and 1.")
        if not self.preserve_patient_grouping:
            raise ValueError("Retraining must preserve patient grouping.")
        if not self.temporal_split:
            raise ValueError("Retraining must preserve temporal separation.")
        return self


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: list[Literal["logistic_regression", "random_forest", "xgboost"]]

    @field_validator("enabled")
    @classmethod
    def _models_required(cls, value: list[str]) -> list[str]:
        required = {"logistic_regression", "random_forest", "xgboost"}
        if set(value) != required:
            raise ValueError(
                "Retraining must configure logistic_regression, random_forest and xgboost."
            )
        return value


class PreprocessingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fit_on_retraining_train_only: bool
    reuse_feature_definition_contract: bool
    reuse_fitted_preprocessor: bool

    @model_validator(mode="after")
    def _safe_preprocessing(self) -> PreprocessingConfig:
        if not self.fit_on_retraining_train_only:
            raise ValueError("Retraining preprocessing must fit on retraining train only.")
        if not self.reuse_feature_definition_contract:
            raise ValueError("Retraining must reuse the Milestone 5 feature-definition contract.")
        if self.reuse_fitted_preprocessor:
            raise ValueError(
                "Retraining must not reuse the old fitted preprocessor as newly fitted."
            )
        return self


class OutputConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_directory: Path
    report_directory: Path
    generated_data_directory: Path

    @field_validator("candidate_directory", "report_directory", "generated_data_directory")
    @classmethod
    def _safe_relative_path(cls, value: Path) -> Path:
        if value.is_absolute() or ".." in value.parts:
            raise ValueError("Retraining output paths must be safe repository-relative paths.")
        return value


class ControlConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    automatic_registration: bool
    automatic_approval: bool
    automatic_activation: bool
    automatic_deployment: bool

    @model_validator(mode="after")
    def _no_automatic_mutation(self) -> ControlConfig:
        if any(
            [
                self.automatic_registration,
                self.automatic_approval,
                self.automatic_activation,
                self.automatic_deployment,
            ]
        ):
            raise ValueError("Milestone 12 controls must not perform automatic model mutation.")
        return self


class RetrainingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    description: str
    implementation_status: Literal["implemented"]
    enabled: bool
    workflow: WorkflowConfig
    eligibility: EligibilityConfig
    dataset: DatasetConfig
    models: ModelConfig
    preprocessing: PreprocessingConfig
    outputs: OutputConfig
    controls: ControlConfig

    @classmethod
    def from_file(cls, path: Path) -> RetrainingConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(payload)


class ComparisonConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    description: str
    implementation_status: Literal["implemented"]
    enabled: bool
    comparison: dict[str, float | str]
    promotion_requirements: dict[str, bool | float]
    selection: dict[str, bool]
    decisions: dict[str, list[str]]

    @model_validator(mode="after")
    def _safe_selection(self) -> ComparisonConfig:
        if self.selection.get("use_historical_test_set_for_selection") is not False:
            raise ValueError("Historical test set must not be used for challenger selection.")
        for key, value in self.promotion_requirements.items():
            if isinstance(value, int | float) and value < 0:
                raise ValueError(f"Promotion threshold must not be negative: {key}")
        return self

    @classmethod
    def from_file(cls, path: Path) -> ComparisonConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(payload)
