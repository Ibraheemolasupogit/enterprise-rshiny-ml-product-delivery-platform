"""Serving readiness validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ml_product.registry.config import GovernanceConfig, RegistryConfig
from ml_product.registry.registry import LocalModelRegistry
from ml_product.serving.config import ServingConfig
from ml_product.serving.loader import resolve_model


def validate_serving(
    *,
    registry_config: RegistryConfig,
    governance_config: GovernanceConfig,
    serving_config: ServingConfig,
    root: Path = Path("."),
) -> dict[str, Any]:
    errors: list[str] = []
    registry = LocalModelRegistry(registry_config, governance_config, root=root)
    registry_result = registry.validate()
    if not registry_result["valid"]:
        errors.extend(registry_result["errors"])
    loaded = resolve_model(
        registry_config=registry_config,
        governance_config=governance_config,
        serving_config=serving_config,
        root=root,
    )
    return {
        "valid": not errors,
        "errors": errors,
        "approved_serving_ready": loaded is not None and not loaded.review_mode,
        "default_ready": loaded is not None,
        "review_mode_default": serving_config.model.allow_registered_candidate_for_local_review,
    }
