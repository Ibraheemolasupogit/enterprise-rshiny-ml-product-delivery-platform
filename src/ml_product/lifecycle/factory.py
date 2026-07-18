"""Lifecycle provider factory."""

from __future__ import annotations

from pathlib import Path

from ml_product.lifecycle.config import LifecycleConfig
from ml_product.lifecycle.local_provider import LocalLifecycleProvider
from ml_product.lifecycle.provider import ModelLifecycleProvider
from ml_product.lifecycle.sas_viya_client import HttpTransport
from ml_product.lifecycle.sas_viya_provider import SasViyaLifecycleProvider


def build_lifecycle_provider(
    config: LifecycleConfig,
    *,
    root: Path = Path("."),
    transport: HttpTransport | None = None,
) -> ModelLifecycleProvider:
    """Build the configured lifecycle provider without changing registry state."""

    if not config.enabled or not config.provider.enabled:
        raise ValueError("Model lifecycle integration is disabled.")
    if config.provider.selected == "local":
        return LocalLifecycleProvider(config.local, root=root)
    if config.provider.selected == "sas_viya":
        if not config.sas_viya.enabled:
            raise ValueError("SAS Viya provider selected but sas_viya.enabled is false.")
        return SasViyaLifecycleProvider(config.sas_viya, transport=transport)
    raise ValueError(f"Unsupported lifecycle provider: {config.provider.selected}")
