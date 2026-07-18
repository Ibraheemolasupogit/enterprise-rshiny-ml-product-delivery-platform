"""Factory for selectable governed logical-view clients."""

from __future__ import annotations

import os
from pathlib import Path

from ml_product.ingestion.config import DatabaseConfig
from ml_product.ingestion.denodo_client import DenodoClient
from ml_product.ingestion.local_view_client import LocalDuckDBViewClient
from ml_product.ingestion.logical_view_client import LogicalViewClient
from ml_product.ingestion.postgresql_view_client import PostgreSQLViewClient


def selected_logical_view_backend(config: DatabaseConfig) -> str:
    backend = os.environ.get(config.engine.denodo.logical_backend_env, config.logical_layer.adapter)
    if backend not in {"duckdb", "postgresql", "denodo"}:
        raise ValueError("LOGICAL_VIEW_BACKEND must be duckdb, postgresql, or denodo")
    return backend


def build_logical_view_client(
    config: DatabaseConfig,
    *,
    database_path: Path | None = None,
    default_limit: int | None = None,
    max_limit: int | None = None,
) -> LogicalViewClient:
    backend = selected_logical_view_backend(config)
    resolved_default = default_limit or config.logical_layer.default_limit
    resolved_max = max_limit or config.logical_layer.max_limit
    if backend == "duckdb":
        return LocalDuckDBViewClient(
            database_path or config.database_path(),
            default_limit=resolved_default,
            max_limit=resolved_max,
        )
    if backend == "postgresql":
        return PostgreSQLViewClient(
            config,
            default_limit=resolved_default,
            max_limit=resolved_max,
        )
    return DenodoClient.from_config(
        config,
        default_limit=resolved_default,
        max_limit=resolved_max,
    )
