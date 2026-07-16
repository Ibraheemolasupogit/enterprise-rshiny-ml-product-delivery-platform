from pathlib import Path

import pytest

from ml_product.ingestion.config import DatabaseConfig


def test_database_config_loads() -> None:
    config = DatabaseConfig.from_file(Path("config/database.yaml"))

    assert config.engine.type == "duckdb"
    assert config.logical_layer.provider == "denodo_compatible_local"
    assert config.logical_layer.allow_arbitrary_sql is False


def test_invalid_provider_fails() -> None:
    data = DatabaseConfig.from_file(Path("config/database.yaml")).model_dump()
    data["logical_layer"]["provider"] = "real_denodo"

    with pytest.raises(ValueError):
        DatabaseConfig.model_validate(data)
