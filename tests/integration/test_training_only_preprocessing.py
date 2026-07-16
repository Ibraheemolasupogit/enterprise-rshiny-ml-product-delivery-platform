from pathlib import Path

from ml_product.features.builder import build_features
from ml_product.features.config import FeatureConfig


def test_training_only_preprocessing_metadata(tmp_path: Path) -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    result = build_features(
        config,
        output_dir=tmp_path / "features",
        evidence_dir=tmp_path / "evidence",
        replace=True,
    )
    metadata = result.preprocessor_metadata
    assert metadata["fitted_on_split"] == "train"
    assert metadata["not_a_predictive_model"] is True
    assert "training_split_fingerprint" in metadata
