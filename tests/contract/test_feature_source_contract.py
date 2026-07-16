from pathlib import Path

from ml_product.features.config import FeatureConfig
from ml_product.features.source import load_source


def test_feature_source_contract() -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    source = load_source(config)
    assert source.frame.shape[0] == 117
    assert source.provider_info["arbitrary_sql_access"] is False
    assert config.source.view == "curated.model_source_view"
    assert "raw." not in config.source.view
