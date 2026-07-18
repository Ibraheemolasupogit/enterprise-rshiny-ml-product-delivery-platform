from pathlib import Path

import pytest

from ml_product.ingestion.client_factory import (
    build_logical_view_client,
    selected_logical_view_backend,
)
from ml_product.ingestion.config import DatabaseConfig
from ml_product.ingestion.denodo_client import DenodoClient, DenodoConnectionError
from ml_product.ingestion.local_view_client import LocalDuckDBViewClient


def test_denodo_client_reports_missing_odbc_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    config = DatabaseConfig.from_file(Path("config/database.yaml"))
    monkeypatch.delenv("DENODO_ODBC_DSN", raising=False)
    client = DenodoClient(config)

    assert client.provider_info()["provider"] == "real_denodo"
    assert client.list_views()
    with pytest.raises(DenodoConnectionError, match="DENODO_ODBC_DSN"):
        client.describe_view("curated.model_source_view")
    assert client.health_check()["healthy"] is False


def test_local_client_rejects_unknown_view() -> None:
    client = LocalDuckDBViewClient(Path("data/processed/ml_product.duckdb"))

    with pytest.raises(ValueError):
        client.describe_view("raw.patients")


def test_logical_view_backend_defaults_to_duckdb(monkeypatch: pytest.MonkeyPatch) -> None:
    config = DatabaseConfig.from_file(Path("config/database.yaml"))
    monkeypatch.delenv("LOGICAL_VIEW_BACKEND", raising=False)

    assert selected_logical_view_backend(config) == "duckdb"
    assert isinstance(build_logical_view_client(config), LocalDuckDBViewClient)


def test_invalid_logical_view_backend_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    config = DatabaseConfig.from_file(Path("config/database.yaml"))
    monkeypatch.setenv("LOGICAL_VIEW_BACKEND", "sqlite")

    with pytest.raises(ValueError, match="LOGICAL_VIEW_BACKEND"):
        selected_logical_view_backend(config)
