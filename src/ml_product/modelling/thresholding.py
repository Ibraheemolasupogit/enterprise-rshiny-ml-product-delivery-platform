"""Validation-only threshold analysis."""

from __future__ import annotations

from typing import Any

import numpy as np

from ml_product.modelling.config import ThresholdConfig
from ml_product.modelling.evaluation import evaluate_predictions


def candidate_thresholds(config: ThresholdConfig) -> list[float]:
    values: list[float] = []
    current = config.thresholds.candidate_values.start
    while current <= config.thresholds.candidate_values.stop + 1e-9:
        values.append(round(current, 10))
        current += config.thresholds.candidate_values.step
    return values


def analyse_thresholds(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    config: ThresholdConfig,
    *,
    prevalence: float,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for threshold in candidate_thresholds(config):
        metrics = evaluate_predictions(
            y_true,
            probabilities,
            threshold=threshold,
            prevalence=prevalence,
        )
        cm = metrics["confusion_matrix"]
        row = {
            "threshold": threshold,
            **cm,
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "specificity": metrics["specificity"],
            "f1": metrics["f1"],
            "balanced_accuracy": metrics["balanced_accuracy"],
            "predicted_positive_rate": metrics["predicted_positive_rate"],
            "false_negative_cost": config.operational_costs.false_negative_cost,
            "false_positive_cost": config.operational_costs.false_positive_cost,
            "total_weighted_cost": (
                cm["false_negatives"] * config.operational_costs.false_negative_cost
                + cm["false_positives"] * config.operational_costs.false_positive_cost
            ),
        }
        rows.append(row)
    eligible = [row for row in rows if row["recall"] >= config.selection.minimum_recall] or rows
    selected = sorted(
        eligible,
        key=lambda row: (
            -row["precision"],
            row["total_weighted_cost"],
            row["threshold"],
        ),
    )[0]
    return {
        "thresholds": rows,
        "selected_threshold": selected["threshold"],
        "selected_row": selected,
        "selection_rule": (
            "Retain thresholds meeting minimum recall, select highest precision, "
            "break ties by lowest weighted cost then lowest threshold."
        ),
    }
