from pathlib import Path

from ml_product.features.config import FeatureConfig
from ml_product.features.metadata import config_fingerprint


def test_config_fingerprint_is_stable() -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    assert config_fingerprint(config) == config_fingerprint(config)
