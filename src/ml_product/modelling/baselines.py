"""Non-informative Milestone 6 baselines."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BaselineModel:
    identifier: str
    probability: float
    majority_class: bool

    def predict_proba(self, row_count: int) -> np.ndarray:
        return np.full(row_count, self.probability, dtype=float)


def fit_prevalence_baseline(y_train: np.ndarray) -> BaselineModel:
    prevalence = float(y_train.astype(bool).mean())
    return BaselineModel(
        identifier="baseline_prevalence",
        probability=prevalence,
        majority_class=prevalence >= 0.5,
    )


def fit_majority_baseline(y_train: np.ndarray) -> BaselineModel:
    prevalence = float(y_train.astype(bool).mean())
    majority = prevalence >= 0.5
    return BaselineModel(
        identifier="baseline_majority_class",
        probability=1.0 if majority else 0.0,
        majority_class=majority,
    )
