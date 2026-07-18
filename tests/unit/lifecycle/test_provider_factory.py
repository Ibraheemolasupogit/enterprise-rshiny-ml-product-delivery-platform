from pathlib import Path

import pytest

from ml_product.lifecycle.config import LifecycleConfig
from ml_product.lifecycle.factory import build_lifecycle_provider
from ml_product.lifecycle.local_provider import LocalLifecycleProvider
from ml_product.lifecycle.sas_viya_provider import SasViyaLifecycleProvider


def test_factory_builds_local_provider_by_default() -> None:
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml"))

    provider = build_lifecycle_provider(config)

    assert isinstance(provider, LocalLifecycleProvider)


def test_factory_requires_enabled_sas_viya_provider() -> None:
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml"))
    payload = config.model_dump()
    payload["provider"]["selected"] = "sas_viya"
    updated = LifecycleConfig.model_validate(payload)

    with pytest.raises(ValueError, match="enabled is false"):
        build_lifecycle_provider(updated)


def test_factory_builds_sas_viya_provider_when_explicitly_enabled() -> None:
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml"))
    payload = config.model_dump()
    payload["provider"]["selected"] = "sas_viya"
    payload["sas_viya"]["enabled"] = True
    updated = LifecycleConfig.model_validate(payload)

    provider = build_lifecycle_provider(updated)

    assert isinstance(provider, SasViyaLifecycleProvider)
