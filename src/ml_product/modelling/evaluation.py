"""Evaluation metrics for Milestone 6 modelling."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_predictions(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    *,
    threshold: float,
    prevalence: float,
    bootstrap_seed: int | None = None,
    bootstrap_iterations: int = 0,
) -> dict[str, Any]:
    y_bool = y_true.astype(bool)
    clipped = np.clip(probabilities.astype(float), 1e-6, 1 - 1e-6)
    predicted = clipped >= threshold
    tn, fp, fn, tp = confusion_matrix(y_bool, predicted, labels=[False, True]).ravel()
    metrics: dict[str, Any] = {
        "roc_auc": _safe_roc_auc(y_bool, clipped),
        "pr_auc": float(average_precision_score(y_bool, clipped)),
        "pr_auc_lift_over_prevalence": float(average_precision_score(y_bool, clipped) - prevalence),
        "brier_score": float(brier_score_loss(y_bool, clipped)),
        "log_loss": float(log_loss(y_bool, clipped, labels=[False, True])),
        "accuracy": float(accuracy_score(y_bool, predicted)),
        "precision": float(precision_score(y_bool, predicted, zero_division=0)),
        "recall": float(recall_score(y_bool, predicted, zero_division=0)),
        "sensitivity": float(recall_score(y_bool, predicted, zero_division=0)),
        "specificity": _safe_divide(tn, tn + fp),
        "f1": float(f1_score(y_bool, predicted, zero_division=0)),
        "negative_predictive_value": _safe_divide(tn, tn + fn),
        "balanced_accuracy": float(balanced_accuracy_score(y_bool, predicted)),
        "predicted_positive_rate": float(predicted.mean()),
        "calibration_error": expected_calibration_error(y_bool, clipped),
        "calibration_intercept": calibration_intercept(y_bool, clipped),
        "calibration_slope": calibration_slope(y_bool, clipped),
        "confusion_matrix": {
            "true_positives": int(tp),
            "false_positives": int(fp),
            "true_negatives": int(tn),
            "false_negatives": int(fn),
        },
        "reliability_bins": reliability_bins(y_bool, clipped),
    }
    if bootstrap_seed is not None and bootstrap_iterations > 0:
        metrics["bootstrap_confidence_intervals"] = bootstrap_intervals(
            y_bool, clipped, threshold, bootstrap_seed, bootstrap_iterations
        )
    return metrics


def expected_calibration_error(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    bins = reliability_bins(y_true, probabilities)
    total = sum(item["count"] for item in bins)
    if total == 0:
        return 0.0
    return float(
        sum(item["count"] * abs(item["observed_rate"] - item["mean_probability"]) for item in bins)
        / total
    )


def reliability_bins(
    y_true: np.ndarray, probabilities: np.ndarray, bins: int = 5
) -> list[dict[str, Any]]:
    edges = np.linspace(0, 1, bins + 1)
    output: list[dict[str, Any]] = []
    for index in range(bins):
        lower = edges[index]
        upper = edges[index + 1]
        mask = (probabilities >= lower) & (
            probabilities <= upper if index == bins - 1 else probabilities < upper
        )
        if not mask.any():
            output.append(
                {
                    "lower": float(lower),
                    "upper": float(upper),
                    "count": 0,
                    "mean_probability": 0.0,
                    "observed_rate": 0.0,
                }
            )
            continue
        output.append(
            {
                "lower": float(lower),
                "upper": float(upper),
                "count": int(mask.sum()),
                "mean_probability": float(probabilities[mask].mean()),
                "observed_rate": float(y_true[mask].mean()),
            }
        )
    return output


def bootstrap_intervals(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
    seed: int,
    iterations: int,
) -> dict[str, dict[str, float]]:
    rng = np.random.default_rng(seed)
    values: dict[str, list[float]] = {
        "roc_auc": [],
        "pr_auc": [],
        "recall": [],
        "precision": [],
        "brier_score": [],
    }
    for _ in range(iterations):
        indices = rng.integers(0, len(y_true), len(y_true))
        sample_y = y_true[indices]
        sample_p = probabilities[indices]
        if len(np.unique(sample_y)) < 2:
            continue
        sample_metrics = evaluate_predictions(
            sample_y,
            sample_p,
            threshold=threshold,
            prevalence=float(sample_y.mean()),
            bootstrap_iterations=0,
        )
        for key in values:
            metric_value = sample_metrics[key]
            if metric_value is not None:
                values[key].append(float(metric_value))
    return {
        key: {
            "lower": float(np.percentile(items, 2.5)) if items else float("nan"),
            "upper": float(np.percentile(items, 97.5)) if items else float("nan"),
        }
        for key, items in values.items()
    }


def calibration_intercept(y_true: np.ndarray, probabilities: np.ndarray) -> float | None:
    if len(np.unique(y_true)) < 2:
        return None
    residual = y_true.astype(float) - probabilities
    return float(residual.mean())


def calibration_slope(y_true: np.ndarray, probabilities: np.ndarray) -> float | None:
    if len(np.unique(y_true)) < 2 or float(np.std(probabilities)) == 0:
        return None
    return float(np.cov(probabilities, y_true.astype(float), ddof=0)[0, 1] / np.var(probabilities))


def _safe_roc_auc(y_true: np.ndarray, probabilities: np.ndarray) -> float | None:
    if len(np.unique(y_true)) < 2:
        return None
    return float(roc_auc_score(y_true, probabilities))


def _safe_divide(numerator: int | float, denominator: int | float) -> float:
    return 0.0 if denominator == 0 else float(numerator / denominator)
