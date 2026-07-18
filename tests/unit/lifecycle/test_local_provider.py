from pathlib import Path

from ml_product.lifecycle.config import LifecycleConfig
from ml_product.lifecycle.factory import build_lifecycle_provider


def test_local_provider_delegates_readiness_to_registry() -> None:
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml"))
    provider = build_lifecycle_provider(config)

    result = provider.readiness_check()

    assert result["provider"] == "local"
    assert result["provider_label"] == "local_model_lifecycle"
    assert result["healthy"] is True


def test_local_provider_retrieves_registry_metadata_without_mutation() -> None:
    registry_path = Path("models/registry.json")
    before = registry_path.read_text(encoding="utf-8")
    config = LifecycleConfig.from_file(Path("config/model_lifecycle.yaml"))
    provider = build_lifecycle_provider(config)

    metadata = provider.retrieve_model_metadata("long_stay_admission_risk", 1)
    response = provider.register_model_package({"model_name": "long_stay_admission_risk"})

    assert metadata["model_name"] == "long_stay_admission_risk"
    assert metadata["registry_version"] == 1
    assert response["accepted"] is False
    assert registry_path.read_text(encoding="utf-8") == before
