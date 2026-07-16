from pathlib import Path

import pytest

from ml_product.modelling.config import ModelTrainingConfig, ThresholdConfig, _safe_path


def test_model_configs_load() -> None:
    config = ModelTrainingConfig.from_file(Path("config/model_training.yaml"))
    thresholds = ThresholdConfig.from_file(Path("config/model_thresholds.yaml"))
    assert config.feature_source.expected_feature_count == 71
    assert thresholds.selection.minimum_recall == 0.8


def test_invalid_threshold_range_fails() -> None:
    payload = ThresholdConfig.from_file(Path("config/model_thresholds.yaml")).model_dump(
        mode="json"
    )
    payload["thresholds"]["candidate_values"]["start"] = 0.9
    with pytest.raises(ValueError, match="Threshold range"):
        ThresholdConfig.model_validate(payload)


def test_negative_cost_fails() -> None:
    payload = ThresholdConfig.from_file(Path("config/model_thresholds.yaml")).model_dump(
        mode="json"
    )
    payload["operational_costs"]["false_negative_cost"] = -1
    with pytest.raises(ValueError, match="Operational costs"):
        ThresholdConfig.model_validate(payload)


def test_unsafe_model_output_path_fails() -> None:
    with pytest.raises(ValueError, match="Unsafe"):
        _safe_path(Path("/etc/model-output"))
