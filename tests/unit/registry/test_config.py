from pathlib import Path

import pytest

from ml_product.registry.config import RegistryConfig


def test_registry_config_loads() -> None:
    config = RegistryConfig.from_file(Path("config/model_registry.yaml"))
    assert config.registry.type == "local_filesystem"
    assert config.approval.automatic_approval is False
    assert config.activation.require_approved_status is True


def test_registry_config_rejects_automatic_approval() -> None:
    payload = RegistryConfig.from_file(Path("config/model_registry.yaml")).model_dump(mode="json")
    payload["approval"]["automatic_approval"] = True
    with pytest.raises(ValueError, match="Automatic approval"):
        RegistryConfig.model_validate(payload)
