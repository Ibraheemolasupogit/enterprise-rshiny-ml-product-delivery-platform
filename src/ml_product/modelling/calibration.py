"""Validation-only probability calibration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from ml_product.modelling.config import ModelTrainingConfig
from ml_product.modelling.evaluation import evaluate_predictions


@dataclass(frozen=True)
class Calibrator:
    method: str
    model: Any | None = None

    def transform(self, probabilities: np.ndarray) -> np.ndarray:
        clipped = np.clip(probabilities, 1e-6, 1 - 1e-6)
        if self.method == "uncalibrated" or self.model is None:
            return np.asarray(clipped, dtype=float)
        if self.method == "sigmoid":
            logits = _logit(clipped).reshape(-1, 1)
            return np.asarray(self.model.predict_proba(logits)[:, 1], dtype=float)
        if self.method == "isotonic":
            return np.asarray(self.model.predict(clipped), dtype=float)
        raise ValueError(f"Unsupported calibration method: {self.method}")


def select_calibration(
    y_validation: np.ndarray,
    validation_probabilities: np.ndarray,
    *,
    threshold: float,
    prevalence: float,
    config: ModelTrainingConfig,
) -> tuple[Calibrator, dict[str, Any]]:
    candidates: dict[str, Calibrator] = {"uncalibrated": Calibrator("uncalibrated")}
    eligibility: dict[str, dict[str, Any]] = {
        "uncalibrated": {"eligible": True, "reason": "reference"},
        "sigmoid": {"eligible": True, "reason": "validation-only Platt calibration"},
        "isotonic": {
            "eligible": len(y_validation)
            >= config.calibration.minimum_validation_rows_for_isotonic,
            "reason": (
                "validation row count below configured minimum"
                if len(y_validation) < config.calibration.minimum_validation_rows_for_isotonic
                else "eligible"
            ),
        },
    }
    sigmoid = LogisticRegression(solver="lbfgs", random_state=config.experiment.random_seed)
    sigmoid.fit(_logit(validation_probabilities).reshape(-1, 1), y_validation)
    candidates["sigmoid"] = Calibrator("sigmoid", sigmoid)
    if eligibility["isotonic"]["eligible"]:
        isotonic = IsotonicRegression(out_of_bounds="clip")
        isotonic.fit(validation_probabilities, y_validation)
        candidates["isotonic"] = Calibrator("isotonic", isotonic)
    metrics: dict[str, dict[str, Any]] = {}
    for method, calibrator in candidates.items():
        transformed = calibrator.transform(validation_probabilities)
        metrics[method] = evaluate_predictions(
            y_validation,
            transformed,
            threshold=threshold,
            prevalence=prevalence,
        )
    uncalibrated_brier = metrics["uncalibrated"]["brier_score"]
    eligible_methods = [
        method
        for method in config.calibration.methods
        if method in metrics
        and metrics[method]["brier_score"]
        <= uncalibrated_brier + config.calibration.maximum_allowed_brier_worsening
    ]
    selected_method = min(
        eligible_methods or ["uncalibrated"],
        key=lambda method: (metrics[method]["brier_score"], method != "uncalibrated", method),
    )
    return candidates[selected_method], {
        "method_eligibility": eligibility,
        "validation_metrics": metrics,
        "selected_method": selected_method,
        "selection_reason": (
            "Selected lowest validation Brier score without material worsening "
            "relative to uncalibrated probabilities."
        ),
    }


def _logit(probabilities: np.ndarray) -> np.ndarray:
    clipped = np.clip(probabilities, 1e-6, 1 - 1e-6)
    return np.asarray(np.log(clipped / (1 - clipped)), dtype=float)
