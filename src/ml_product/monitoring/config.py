"""Typed monitoring configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MonitoringBaselineConfig(BaseModel):
    source: Literal["training_features"]
    reference_split: Literal["train"]
    minimum_rows: int = Field(ge=1)


class MonitoringWindowConfig(BaseModel):
    minimum_unlabelled_rows: int = Field(ge=1)
    minimum_labelled_rows: int = Field(ge=1)
    event_window_size: int = Field(ge=1)
    maximum_rows: int = Field(ge=1, le=10000)


class MonitoringSchemaConfig(BaseModel):
    fail_on_missing_required_column: bool
    fail_on_unexpected_column: bool
    fail_on_type_change: bool


class MonitoringDataQualityConfig(BaseModel):
    missingness_warning_increase: float = Field(ge=0, le=1)
    missingness_critical_increase: float = Field(ge=0, le=1)
    invalid_value_warning_rate: float = Field(ge=0, le=1)
    invalid_value_critical_rate: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_order(self) -> MonitoringDataQualityConfig:
        if self.missingness_warning_increase >= self.missingness_critical_increase:
            raise ValueError("Missingness warning threshold must be below critical.")
        if self.invalid_value_warning_rate >= self.invalid_value_critical_rate:
            raise ValueError("Invalid-value warning threshold must be below critical.")
        return self


class MonitoringPerformanceConfig(BaseModel):
    evaluate_when_labels_available: bool
    minimum_labelled_rows: int = Field(ge=1)
    minimum_positive_rows: int = Field(ge=1)
    minimum_negative_rows: int = Field(ge=1)


class MonitoringAlertConfig(BaseModel):
    review_required_on_warning: bool
    review_required_on_critical: bool
    automatic_retraining: bool
    automatic_model_replacement: bool

    @model_validator(mode="after")
    def reject_automation(self) -> MonitoringAlertConfig:
        if self.automatic_retraining or self.automatic_model_replacement:
            raise ValueError("Monitoring alerts must not trigger automatic model changes.")
        return self


class MonitoringOutputConfig(BaseModel):
    directory: Path
    committed_evidence_directory: Path

    @field_validator("directory", "committed_evidence_directory")
    @classmethod
    def reject_unsafe_path(cls, value: Path) -> Path:
        if value.is_absolute() or ".." in value.parts:
            raise ValueError("Monitoring output paths must be repository-relative.")
        return value


class MonitoringConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    version: int
    description: str
    implementation_status: Literal["implemented"]
    enabled: bool
    baseline: MonitoringBaselineConfig
    windows: MonitoringWindowConfig
    schema_checks: MonitoringSchemaConfig = Field(alias="schema")
    data_quality: MonitoringDataQualityConfig
    performance: MonitoringPerformanceConfig
    alerts: MonitoringAlertConfig
    outputs: MonitoringOutputConfig

    @classmethod
    def from_file(cls, path: Path) -> MonitoringConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a YAML mapping.")
        return cls.model_validate(payload)


class LevelThreshold(BaseModel):
    warning: float = Field(ge=0)
    critical: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_order(self) -> LevelThreshold:
        if self.warning >= self.critical:
            raise ValueError("Warning threshold must be below critical threshold.")
        return self


class PValueThreshold(BaseModel):
    warning_p_value: float = Field(gt=0, le=1)
    critical_p_value: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def validate_order(self) -> PValueThreshold:
        if self.critical_p_value >= self.warning_p_value:
            raise ValueError("Critical p-value must be below warning p-value.")
        return self


class WassersteinConfig(BaseModel):
    enabled: bool
    normalise: bool


class NumericThresholds(BaseModel):
    psi: LevelThreshold
    ks: PValueThreshold
    wasserstein: WassersteinConfig


class CategoricalThresholds(BaseModel):
    jensen_shannon: LevelThreshold
    chi_square: PValueThreshold


class PredictionThresholds(BaseModel):
    psi: LevelThreshold
    mean_probability_change: LevelThreshold
    positive_rate_change: LevelThreshold


class PerformanceThresholds(BaseModel):
    pr_auc_drop: LevelThreshold
    roc_auc_drop: LevelThreshold
    brier_increase: LevelThreshold
    recall_drop: LevelThreshold
    specificity_drop: LevelThreshold
    calibration_error_increase: LevelThreshold


class OperationalThresholds(BaseModel):
    p95_latency_ms: LevelThreshold
    error_rate: LevelThreshold


class DriftThresholdConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    description: str
    implementation_status: Literal["implemented"]
    enabled: bool
    numeric: NumericThresholds
    categorical: CategoricalThresholds
    prediction: PredictionThresholds
    performance: PerformanceThresholds
    operational: OperationalThresholds

    @classmethod
    def from_file(cls, path: Path) -> DriftThresholdConfig:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{path} must contain a YAML mapping.")
        return cls.model_validate(payload)
