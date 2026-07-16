from pathlib import Path

import numpy as np
import pandas as pd

from ml_product.modelling.config import ModelTrainingConfig
from ml_product.modelling.prediction import predict_probability
from ml_product.modelling.xgboost_model import train_xgboost


def test_xgboost_candidate_imports_fits_and_predicts_probabilities() -> None:
    config = ModelTrainingConfig.from_file(Path("config/model_training.yaml"))
    x_train = pd.DataFrame(
        {
            "clinical_score": [0.0, 0.2, 0.4, 1.0, 1.2, 1.4],
            "capacity_pressure": [0.1, 0.3, 0.2, 0.8, 0.9, 0.7],
        }
    )
    y_train = np.array([False, False, False, True, True, True])

    model, metadata = train_xgboost(x_train, y_train, config)
    probabilities = predict_probability(model, x_train)

    assert metadata["identifier"] == "xgboost"
    assert metadata["fit_status"] == "fitted"
    assert metadata["parameters"]["objective"] == "binary:logistic"
    assert metadata["parameters"]["eval_metric"] == "logloss"
    assert metadata["parameters"]["tree_method"] == "hist"
    assert metadata["parameters"]["device"] == "cpu"
    assert np.all((probabilities >= 0.0) & (probabilities <= 1.0))
