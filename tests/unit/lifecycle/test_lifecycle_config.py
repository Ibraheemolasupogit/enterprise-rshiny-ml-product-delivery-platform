from pathlib import Path

import pytest
from pydantic import ValidationError

from ml_product.lifecycle.config import LifecycleConfig


def test_lifecycle_config_defaults_to_local_provider() -> None:
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml"))

    assert config.provider.selected == "local"
    assert config.local.provider_label == "local_model_lifecycle"
    assert config.sas_viya.access_token_env == "SAS_VIYA_ACCESS_TOKEN"


def test_lifecycle_config_rejects_invalid_sas_base_url() -> None:
    payload = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml")).model_dump()
    payload["sas_viya"]["base_url"] = "sas-viya.example.local"

    with pytest.raises(ValidationError, match="base_url"):
        LifecycleConfig.model_validate(payload)
