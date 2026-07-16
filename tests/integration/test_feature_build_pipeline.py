from pathlib import Path

from ml_product.features.builder import build_features
from ml_product.features.config import FeatureConfig
from ml_product.features.validation import validate_feature_outputs


def test_feature_build_pipeline_writes_outputs(tmp_path: Path) -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    result = build_features(
        config,
        output_dir=tmp_path / "features",
        evidence_dir=tmp_path / "evidence",
        replace=True,
    )
    assert result.manifest["counts"]["source_row_count"] == 117
    assert result.leakage_report["total_violations"] == 0
    validation = validate_feature_outputs(
        config,
        output_dir=tmp_path / "features",
        evidence_dir=tmp_path / "evidence",
    )
    assert validation["valid"], validation["errors"]
