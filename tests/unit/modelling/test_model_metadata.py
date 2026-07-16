from pathlib import Path

from ml_product.modelling.config import ModelTrainingConfig, ThresholdConfig
from ml_product.modelling.metadata import config_fingerprint


def test_training_fingerprint_is_stable() -> None:
    config = ModelTrainingConfig.from_file(Path("config/model_training.yaml"))
    thresholds = ThresholdConfig.from_file(Path("config/model_thresholds.yaml"))
    assert config_fingerprint(config, thresholds) == config_fingerprint(config, thresholds)
