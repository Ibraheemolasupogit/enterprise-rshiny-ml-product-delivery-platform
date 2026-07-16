from pathlib import Path

import pytest

from ml_product.serving.config import ServingConfig


def test_serving_config_loads_review_mode_disabled() -> None:
    config = ServingConfig.from_file(Path("config/serving.yaml"))
    assert config.model.allow_registered_candidate_for_local_review is False
    assert config.security.api_key_environment_variable == "MODEL_API_KEY"


def test_serving_config_rejects_review_mode_enabled_by_default() -> None:
    payload = ServingConfig.from_file(Path("config/serving.yaml")).model_dump(mode="json")
    payload["model"]["allow_registered_candidate_for_local_review"] = True
    with pytest.raises(ValueError, match="Review mode"):
        ServingConfig.model_validate(payload)
