"""FastAPI dependency helpers."""

from __future__ import annotations

from dataclasses import dataclass

from ml_product.serving.config import ServingConfig
from ml_product.serving.loader import LoadedModel


@dataclass
class AppState:
    config: ServingConfig
    loaded_model: LoadedModel | None
