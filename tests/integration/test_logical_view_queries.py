from ml_product.ingestion.config import DatabaseConfig
from ml_product.ingestion.local_view_client import LocalDuckDBViewClient


def test_logical_view_client_queries_allowed_view() -> None:
    config = DatabaseConfig.from_file(__import__("pathlib").Path("config/database.yaml"))
    client = LocalDuckDBViewClient(config.database_path())

    rows = client.query_view("curated.model_source_view", columns=["admission_id"], limit=2)

    assert len(rows) == 2
    assert set(rows[0]) == {"admission_id"}
    assert client.provider_info()["provider"] == "denodo_compatible_local"
