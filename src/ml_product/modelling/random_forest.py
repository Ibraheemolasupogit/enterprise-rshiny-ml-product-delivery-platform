"""Deterministic Random Forest candidate."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from ml_product.modelling.config import ModelTrainingConfig


def train_random_forest(
    x_train: pd.DataFrame, y_train: np.ndarray, config: ModelTrainingConfig
) -> tuple[RandomForestClassifier, dict[str, Any]]:
    params = dict(config.models.random_forest.parameters)
    model = RandomForestClassifier(**params, random_state=config.experiment.random_seed)
    model.fit(x_train, y_train)
    importance = [
        {"feature_name": feature, "importance": float(value)}
        for feature, value in zip(x_train.columns, model.feature_importances_, strict=True)
    ]
    return model, {
        "identifier": "random_forest",
        "fit_status": "fitted",
        "parameters": params,
        "native_feature_importance": sorted(
            importance, key=lambda item: item["importance"], reverse=True
        ),
    }
