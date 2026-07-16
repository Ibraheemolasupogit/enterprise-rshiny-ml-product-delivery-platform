from pathlib import Path

from ml_product.features.config import FeatureConfig
from ml_product.features.eligibility import apply_eligibility
from ml_product.features.source import load_source
from ml_product.features.temporal import add_temporal_features


def test_eligibility_counts_reconcile() -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    source = load_source(config)
    result = apply_eligibility(add_temporal_features(source.frame), config)
    assert result.summary["source_count"] == (
        result.summary["eligible_count"] + result.summary["excluded_count"]
    )
    assert result.summary["duplicate_admission_count"] == 0
