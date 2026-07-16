from pathlib import Path

import pytest

from ml_product.features.config import FeatureConfig, _resolve_safe_path


def test_feature_config_loads() -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    assert config.source.view == "curated.model_source_view"
    assert config.prediction_contract.target_column == "long_stay_flag_governed"
    assert "long_stay_flag_governed" not in config.features.predictors


def test_duplicate_features_fail() -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    payload = config.model_dump(mode="json")
    payload["features"]["categorical"].append(payload["features"]["numeric"][0])
    with pytest.raises(ValueError, match="Duplicate"):
        FeatureConfig.model_validate(payload)


def test_target_and_identifier_as_predictor_fail() -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    payload = config.model_dump(mode="json")
    payload["features"]["numeric"].append("long_stay_flag_governed")
    with pytest.raises(ValueError, match="Target"):
        FeatureConfig.model_validate(payload)
    payload = config.model_dump(mode="json")
    payload["features"]["categorical"].append("patient_id")
    with pytest.raises(ValueError, match="Prohibited"):
        FeatureConfig.model_validate(payload)


def test_unsafe_output_path_fails() -> None:
    with pytest.raises(ValueError, match="Unsafe"):
        _resolve_safe_path(Path("/etc/ml-product-features"))
