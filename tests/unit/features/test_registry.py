from pathlib import Path

from ml_product.features.config import FeatureConfig
from ml_product.features.eligibility import apply_eligibility
from ml_product.features.registry import build_feature_registry
from ml_product.features.source import load_source
from ml_product.features.splitting import split_dataset
from ml_product.features.temporal import add_temporal_features
from ml_product.features.transformers import fit_preprocessor


def test_registry_covers_output_features() -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    source = load_source(config)
    eligible = apply_eligibility(add_temporal_features(source.frame), config).eligible
    split = split_dataset(eligible, config)
    train = split.frame[split.frame["split"] == "train"]
    preprocessor = fit_preprocessor(train, config)
    registry = build_feature_registry(config, preprocessor)
    assert registry["coverage_valid"]
    assert registry["registry_entry_count"] == len(preprocessor.output_columns)
