"""Prediction helpers."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def predict_probability(model: Any, features: pd.DataFrame) -> np.ndarray:
    probabilities = model.predict_proba(features)
    return np.asarray(probabilities[:, 1], dtype=float)
