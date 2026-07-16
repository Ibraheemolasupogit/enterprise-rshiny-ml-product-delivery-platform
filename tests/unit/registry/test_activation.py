from pathlib import Path

import pytest

from ml_product.registry.activation import build_activation_event
from ml_product.registry.config import GovernanceConfig, RegistryConfig
from ml_product.registry.registry import LocalModelRegistry


def test_registered_model_cannot_activate() -> None:
    registry = LocalModelRegistry(
        RegistryConfig.from_file(Path("config/model_registry.yaml")),
        GovernanceConfig.from_file(Path("config/model_governance.yaml")),
    )
    version = registry.get_model_version("long_stay_admission_risk", 1)
    with pytest.raises(ValueError, match="Only approved"):
        build_activation_event(
            version=version,
            actor="LOCAL-GOVERNANCE-REVIEWER",
            reason="Not allowed",
            previous_active_version=None,
        )
