from pathlib import Path

from ml_product.features.config import FeatureConfig
from ml_product.features.source import load_source


def test_source_uses_governed_view_client() -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    source = load_source(config)
    assert source.provider_info["provider"] == "denodo_compatible_local"
    assert source.provider_info["arbitrary_sql_access"] is False
    assert "curated.model_source_view" in config.source.view
    assert source.frame["admission_id"].is_unique
