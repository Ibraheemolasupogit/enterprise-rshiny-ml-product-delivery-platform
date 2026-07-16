from pathlib import Path

import numpy as np

from ml_product.modelling.config import ModelTrainingConfig
from ml_product.modelling.data import load_model_data
from ml_product.modelling.fairness import build_fairness_report


def test_fairness_report_suppresses_small_groups() -> None:
    config = ModelTrainingConfig.from_file(Path("config/model_training.yaml"))
    data = load_model_data(config)
    test = data.splits["test"]
    report = build_fairness_report(
        features=test.features,
        target=test.target.to_numpy(dtype=bool),
        probabilities=np.full(len(test.target), 0.8),
        threshold=0.5,
        preprocessor_metadata=data.preprocessor_metadata,
        minimum_group_size=10,
    )
    assert "sex" in report["groups"]
    assert report["limitations"]
