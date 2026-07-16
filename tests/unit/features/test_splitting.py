from pathlib import Path

from ml_product.features.config import FeatureConfig
from ml_product.features.eligibility import apply_eligibility
from ml_product.features.source import load_source
from ml_product.features.splitting import split_dataset
from ml_product.features.temporal import add_temporal_features


def test_split_is_deterministic_and_grouped() -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    source = load_source(config)
    eligible = apply_eligibility(add_temporal_features(source.frame), config).eligible
    first = split_dataset(eligible, config)
    second = split_dataset(eligible, config)
    assert first.fingerprint == second.fingerprint
    assert first.summary["patient_overlap_count"] == 0
    assert first.summary["admission_overlap_count"] == 0
    assert all(
        first.summary["splits"][split]["row_count"] > 0 for split in ("train", "validation", "test")
    )
