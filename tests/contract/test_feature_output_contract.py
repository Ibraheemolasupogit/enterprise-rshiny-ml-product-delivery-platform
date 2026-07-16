from pathlib import Path

import pandas as pd

from ml_product.features.config import FeatureConfig
from ml_product.features.validation import validate_feature_outputs


def test_committed_feature_output_contract() -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    result = validate_feature_outputs(config)
    assert result["valid"], result["errors"]
    output_dir = config.resolved_output_directory()
    train = pd.read_parquet(output_dir / "train_features.parquet")
    validation = pd.read_parquet(output_dir / "validation_features.parquet")
    test = pd.read_parquet(output_dir / "test_features.parquet")
    assert list(train.columns) == list(validation.columns) == list(test.columns)
    assert "admission_id" not in train.columns
    assert "long_stay_flag_governed" not in train.columns
