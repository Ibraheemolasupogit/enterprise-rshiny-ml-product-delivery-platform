from pathlib import Path

import pytest

from ml_product.synthetic_data.config import SyntheticDataConfig


def test_config_loads() -> None:
    config = SyntheticDataConfig.from_file(Path("config/synthetic_data.yaml"))

    assert config.dataset.seed == 20260714
    assert config.dataset.mode == "sample"
    assert config.fingerprint()


def test_invalid_date_range_fails() -> None:
    config = SyntheticDataConfig.from_file(Path("config/synthetic_data.yaml")).model_dump()
    config["dataset"]["end_date"] = "2024-01-01"

    with pytest.raises(ValueError, match="end_date"):
        SyntheticDataConfig.model_validate(config)


def test_invalid_quality_rate_fails() -> None:
    config = SyntheticDataConfig.from_file(Path("config/synthetic_data.yaml")).model_dump()
    config["quality_issues"]["rates"]["missing_mobility_status"] = 1.5

    with pytest.raises(ValueError, match="quality issue rate"):
        SyntheticDataConfig.model_validate(config)


def test_full_mode_cannot_target_sample() -> None:
    config = SyntheticDataConfig.from_file(Path("config/synthetic_data.yaml")).model_dump()
    config["dataset"]["mode"] = "full"

    with pytest.raises(ValueError, match="data/sample"):
        SyntheticDataConfig.model_validate(config)
