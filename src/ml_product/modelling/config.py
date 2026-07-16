"""Typed configuration for Milestone 6 model development."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, model_validator

from ml_product.utils.paths import repository_root

SUPPORTED_MODELS = {"logistic_regression", "random_forest", "xgboost"}
SUPPORTED_CALIBRATION = {"uncalibrated", "sigmoid", "isotonic"}


class ExperimentConfig(BaseModel):
    name: str
    random_seed: int
    target_column: Literal["long_stay_flag_governed"]
    positive_class: bool
    prediction_point: str


class FeatureSourceConfig(BaseModel):
    directory: Path
    manifest: Path
    registry: Path
    split_summary: Path
    leakage_report: Path
    preprocessor_metadata: Path
    expected_feature_count: int


class BaselineSwitch(BaseModel):
    enabled: bool = True


class BaselineConfig(BaseModel):
    prevalence: BaselineSwitch
    majority_class: BaselineSwitch


class ModelSwitch(BaseModel):
    enabled: bool
    parameters: dict[str, Any] = Field(default_factory=dict)


class ModelsConfig(BaseModel):
    logistic_regression: ModelSwitch
    random_forest: ModelSwitch
    xgboost: ModelSwitch


class CalibrationConfig(BaseModel):
    methods: list[Literal["uncalibrated", "sigmoid", "isotonic"]]
    selection_metric: Literal["brier_score"]
    minimum_validation_rows_for_isotonic: int
    maximum_allowed_brier_worsening: float = 0.0

    @model_validator(mode="after")
    def validate_methods(self) -> CalibrationConfig:
        if len(set(self.methods)) != len(self.methods):
            raise ValueError("Calibration methods must be unique.")
        return self


class EvaluationConfig(BaseModel):
    bootstrap_iterations: int
    bootstrap_seed: int


class ExplainabilityConfig(BaseModel):
    permutation_importance: dict[str, Any]
    coefficient_analysis: dict[str, Any]
    tree_importance: dict[str, Any]
    local_explanations: dict[str, Any]


class FairnessConfig(BaseModel):
    groups: list[Literal["sex", "age_band", "deprivation_group"]]
    minimum_group_size: int


class SelectionConfig(BaseModel):
    allow_no_candidate: bool
    prefer_simpler_within_pr_auc: float


class OutputConfig(BaseModel):
    candidate_directory: Path
    report_directory: Path
    overwrite: bool = False


class ModelTrainingConfig(BaseModel):
    version: int
    description: str
    implementation_status: Literal["implemented"]
    enabled: bool
    experiment: ExperimentConfig
    feature_source: FeatureSourceConfig
    baselines: BaselineConfig
    models: ModelsConfig
    calibration: CalibrationConfig
    evaluation: EvaluationConfig
    explainability: ExplainabilityConfig
    fairness: FairnessConfig
    selection: SelectionConfig
    outputs: OutputConfig

    @classmethod
    def from_file(cls, path: Path = Path("config/model_training.yaml")) -> ModelTrainingConfig:
        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)
        if not isinstance(payload, dict):
            raise ValueError("Model training configuration must be a YAML mapping.")
        return cls.model_validate(payload)

    @model_validator(mode="after")
    def validate_model_config(self) -> ModelTrainingConfig:
        if self.feature_source.expected_feature_count != 71:
            raise ValueError("Milestone 6 expects 71 transformed features.")
        if self.models.random_forest.parameters.get("n_jobs") != 1:
            raise ValueError("Random Forest must use n_jobs=1 for deterministic evidence.")
        if self.models.xgboost.parameters.get("n_jobs") != 1:
            raise ValueError("XGBoost must use n_jobs=1 for deterministic evidence.")
        return self

    def feature_directory(self, override: Path | None = None) -> Path:
        return _safe_path(override or self.feature_source.directory)

    def candidate_directory(self, override: Path | None = None) -> Path:
        return _safe_path(override or self.outputs.candidate_directory)

    def report_directory(self, override: Path | None = None) -> Path:
        return _safe_path(override or self.outputs.report_directory)


class ThresholdRange(BaseModel):
    start: float
    stop: float
    step: float

    @model_validator(mode="after")
    def validate_range(self) -> ThresholdRange:
        if not 0 <= self.start < self.stop <= 1:
            raise ValueError("Threshold range must be within [0, 1] with start < stop.")
        if self.step <= 0:
            raise ValueError("Threshold step must be positive.")
        return self


class ThresholdsConfig(BaseModel):
    candidate_values: ThresholdRange


class ThresholdSelectionConfig(BaseModel):
    primary_rule: Literal["minimum_recall"]
    minimum_recall: float
    secondary_metric: Literal["precision"]
    tertiary_metric: Literal["total_weighted_cost"]
    final_tie_break: Literal["lowest_threshold"]

    @model_validator(mode="after")
    def validate_selection(self) -> ThresholdSelectionConfig:
        if not 0 <= self.minimum_recall <= 1:
            raise ValueError("Minimum recall must be a probability.")
        return self


class OperationalCostsConfig(BaseModel):
    false_negative_cost: float
    false_positive_cost: float

    @model_validator(mode="after")
    def validate_costs(self) -> OperationalCostsConfig:
        if self.false_negative_cost < 0 or self.false_positive_cost < 0:
            raise ValueError("Operational costs must be non-negative.")
        return self


class RiskBand(BaseModel):
    minimum: float
    maximum: float


class ThresholdConfig(BaseModel):
    version: int
    description: str
    implementation_status: Literal["implemented"]
    enabled: bool
    thresholds: ThresholdsConfig
    selection: ThresholdSelectionConfig
    operational_costs: OperationalCostsConfig
    risk_bands: dict[str, RiskBand]

    @classmethod
    def from_file(cls, path: Path = Path("config/model_thresholds.yaml")) -> ThresholdConfig:
        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)
        if not isinstance(payload, dict):
            raise ValueError("Threshold configuration must be a YAML mapping.")
        return cls.model_validate(payload)


def _safe_path(path: Path) -> Path:
    root = repository_root().resolve()
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve()
    tmp_root = Path(tempfile.gettempdir()).resolve()
    private_tmp = Path("/private/tmp").resolve()
    if (
        not resolved.is_relative_to(root)
        and not resolved.is_relative_to(tmp_root)
        and not resolved.is_relative_to(private_tmp)
    ):
        raise ValueError(f"Unsafe path outside repository or temporary directory: {path}")
    return resolved
