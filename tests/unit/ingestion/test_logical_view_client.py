from pathlib import Path

import pytest

from ml_product.ingestion.denodo_client import DenodoClient
from ml_product.ingestion.local_view_client import LocalDuckDBViewClient


def test_denodo_client_is_not_implemented() -> None:
    client = DenodoClient()

    assert client.provider_info()["implemented"] is False
    with pytest.raises(NotImplementedError):
        client.list_views()


def test_local_client_rejects_unknown_view() -> None:
    client = LocalDuckDBViewClient(Path("data/processed/ml_product.duckdb"))

    with pytest.raises(ValueError):
        client.describe_view("raw.patients")
