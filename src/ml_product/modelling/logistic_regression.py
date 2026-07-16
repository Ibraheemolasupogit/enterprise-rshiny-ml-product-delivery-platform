"""Deterministic logistic-regression candidate."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from ml_product.modelling.config import ModelTrainingConfig


def train_logistic_regression(
    x_train: pd.DataFrame, y_train: np.ndarray, config: ModelTrainingConfig
) -> tuple[LogisticRegression, dict[str, Any]]:
    params = dict(config.models.logistic_regression.parameters)
    model = LogisticRegression(**params, random_state=config.experiment.random_seed)
    model.fit(x_train, y_train)
    if int(model.n_iter_[0]) >= int(params["max_iter"]):
        raise ValueError("Logistic regression did not converge before max_iter.")
    coefficients = [
        {
            "feature_name": feature,
            "coefficient": float(coef),
            "odds_ratio": float(np.exp(np.clip(coef, -20, 20))),
            "direction": "positive" if coef > 0 else "negative" if coef < 0 else "zero",
        }
        for feature, coef in zip(x_train.columns, model.coef_[0], strict=True)
    ]
    return model, {
        "identifier": "logistic_regression",
        "fit_status": "converged",
        "n_iter": int(model.n_iter_[0]),
        "intercept": float(model.intercept_[0]),
        "coefficients": coefficients,
    }
