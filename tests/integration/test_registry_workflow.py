from pathlib import Path

import pytest

from ml_product.registry.config import GovernanceConfig, RegistryConfig
from ml_product.registry.registry import LocalModelRegistry


def test_duplicate_real_candidate_registration_rejected() -> None:
    registry = LocalModelRegistry(
        RegistryConfig.from_file(Path("config/model_registry.yaml")),
        GovernanceConfig.from_file(Path("config/model_governance.yaml")),
    )
    with pytest.raises(ValueError, match="already registered"):
        registry.register_candidate(
            candidate_identifier="CAND-85EA9202CAD6FE7F",
            model_config_path=Path("config/model_training.yaml"),
            candidate_dir=Path("models/candidate"),
        )
