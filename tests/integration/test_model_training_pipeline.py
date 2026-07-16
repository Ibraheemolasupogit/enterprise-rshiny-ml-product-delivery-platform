from pathlib import Path

from ml_product.modelling.config import ModelTrainingConfig, ThresholdConfig
from ml_product.modelling.training import train_models
from ml_product.modelling.validation import validate_model_outputs


def test_model_training_pipeline_writes_evidence(tmp_path: Path) -> None:
    config = ModelTrainingConfig.from_file(Path("config/model_training.yaml"))
    thresholds = ThresholdConfig.from_file(Path("config/model_thresholds.yaml"))
    result = train_models(
        config,
        thresholds,
        candidate_dir=tmp_path / "candidate",
        report_dir=Path("reports/model_evaluation"),
        replace=True,
    )
    assert result.candidate_recommendation["test_set_used_for_selection"] is False
    assert (tmp_path / "candidate" / "xgboost.json").is_file()
    families = {row["model_family"] for row in result.validation_metrics["rows"]}
    assert "xgboost" in families
    assert result.manifest["candidate_training_status"]["xgboost"]["training_status"] == "fitted"
    validation = validate_model_outputs(config)
    assert validation["valid"], validation["errors"]
