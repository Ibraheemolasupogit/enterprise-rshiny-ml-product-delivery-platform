from pathlib import Path

import pytest

from ml_product.registry.config import GovernanceConfig, RegistryConfig
from ml_product.registry.registry import LocalModelRegistry
from ml_product.registry.rollback import build_rollback_event


def test_unapproved_real_version_is_not_valid_rollback_target() -> None:
    registry = LocalModelRegistry(
        RegistryConfig.from_file(Path("config/model_registry.yaml")),
        GovernanceConfig.from_file(Path("config/model_governance.yaml")),
    )
    version = registry.get_model_version("long_stay_admission_risk", 1)
    with pytest.raises(ValueError, match="approved-compatible"):
        build_rollback_event(
            target=version,
            actor="LOCAL-GOVERNANCE-REVIEWER",
            reason="Fixture validation",
            dry_run=True,
        )
