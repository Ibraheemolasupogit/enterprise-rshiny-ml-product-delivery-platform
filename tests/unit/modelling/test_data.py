from pathlib import Path

from ml_product.modelling.config import ModelTrainingConfig
from ml_product.modelling.data import load_model_data


def test_model_data_contract_loads() -> None:
    config = ModelTrainingConfig.from_file(Path("config/model_training.yaml"))
    data = load_model_data(config)
    assert len(data.feature_names) == 71
    assert data.split_summary["patient_overlap_count"] == 0
    assert data.leakage_report["total_violations"] == 0
    assert list(data.splits["train"].features.columns) == list(data.splits["test"].features.columns)
