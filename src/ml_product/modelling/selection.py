"""Validation-only candidate recommendation."""

from __future__ import annotations

from typing import Any

from ml_product.modelling.config import ModelTrainingConfig

MODEL_COMPLEXITY = {"logistic_regression": 1, "random_forest": 2, "xgboost": 3}


def recommend_candidate(
    validation_rows: list[dict[str, Any]],
    *,
    prevalence_brier: float,
    config: ModelTrainingConfig,
) -> dict[str, Any]:
    candidate_rows = [
        row
        for row in validation_rows
        if row["model_family"] in MODEL_COMPLEXITY
        and row["recall"] >= 0.8
        and row["brier_score"] <= prevalence_brier
    ]
    if not candidate_rows and config.selection.allow_no_candidate:
        return {
            "recommended_model": None,
            "recommendation_status": "no_candidate_meets_requirements",
            "selection_evidence": "No candidate met recall and probability-quality requirements.",
        }
    best_pr_auc = max(row["pr_auc"] for row in candidate_rows)
    close = [
        row
        for row in candidate_rows
        if best_pr_auc - row["pr_auc"] <= config.selection.prefer_simpler_within_pr_auc
    ]
    selected = sorted(
        close,
        key=lambda row: (
            row["brier_score"],
            MODEL_COMPLEXITY[row["model_family"]],
            -row["pr_auc"],
        ),
    )[0]
    return {
        "recommended_model": selected["model_family"],
        "recommendation_status": "recommended_for_registration_review",
        "selection_evidence": (
            "Selected using validation metrics only: minimum recall, Brier score no worse "
            "than prevalence baseline, probability quality, and simpler-model preference."
        ),
    }
