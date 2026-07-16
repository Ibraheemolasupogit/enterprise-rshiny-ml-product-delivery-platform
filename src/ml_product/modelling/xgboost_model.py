"""Deterministic XGBoost candidate."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ml_product.modelling.config import ModelTrainingConfig


def train_xgboost(
    x_train: pd.DataFrame, y_train: np.ndarray, config: ModelTrainingConfig
) -> tuple[Any, dict[str, Any]]:
    try:
        from xgboost import XGBClassifier
    except ImportError as exc:  # pragma: no cover - exercised only when dependency is absent
        raise RuntimeError("xgboost is required for the configured XGBoost candidate.") from exc
    params = dict(config.models.xgboost.parameters)
    model = XGBClassifier(
        **params,
        random_state=config.experiment.random_seed,
        tree_method="hist",
        device="cpu",
    )
    model.fit(x_train, y_train)
    booster = model.get_booster()
    native = booster.get_score(importance_type="gain")
    importance = []
    for feature in x_train.columns:
        raw_value = native.get(feature, 0.0)
        value = raw_value[0] if isinstance(raw_value, list) else raw_value
        importance.append({"feature_name": feature, "importance": float(value)})
    return model, {
        "identifier": "xgboost",
        "fit_status": "fitted",
        "parameters": {**params, "tree_method": "hist", "device": "cpu"},
        "native_feature_importance": sorted(
            importance, key=lambda item: item["importance"], reverse=True
        ),
        "determinism_limitations": (
            "XGBoost is configured single-threaded on CPU; small floating-point differences "
            "can still occur across library/platform versions."
        ),
    }
