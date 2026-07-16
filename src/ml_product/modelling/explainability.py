"""Deterministic global and local explanation evidence."""

from __future__ import annotations

from typing import Any, cast

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance

from ml_product.modelling.config import ModelTrainingConfig


def build_explainability(
    *,
    model: Any,
    model_family: str,
    feature_names: list[str],
    validation_features: pd.DataFrame,
    validation_target: np.ndarray,
    test_features: pd.DataFrame,
    test_target: np.ndarray,
    test_identifiers: pd.DataFrame,
    test_probabilities: np.ndarray,
    threshold: float,
    model_metadata: dict[str, Any],
    config: ModelTrainingConfig,
) -> tuple[dict[str, Any], dict[str, Any]]:
    global_evidence = build_global_explainability(
        model=model,
        model_family=model_family,
        feature_names=feature_names,
        validation_features=validation_features,
        validation_target=validation_target,
        model_metadata=model_metadata,
        config=config,
    )
    local = build_local_explanations(
        test_features=test_features,
        test_target=test_target,
        test_identifiers=test_identifiers,
        probabilities=test_probabilities,
        threshold=threshold,
        feature_evidence=global_evidence,
    )
    return global_evidence, local


def build_global_explainability(
    *,
    model: Any,
    model_family: str,
    feature_names: list[str],
    validation_features: pd.DataFrame,
    validation_target: np.ndarray,
    model_metadata: dict[str, Any],
    config: ModelTrainingConfig,
) -> dict[str, Any]:
    global_evidence: dict[str, Any] = {
        "model_family": model_family,
        "small_sample_warning": (
            "Validation-set importance is directionally useful only because the synthetic "
            "validation set is small."
        ),
        "non_causal_warning": (
            "Feature importance and coefficients describe associations in synthetic data; "
            "they are not causal effects."
        ),
        "permutation_importance": [],
        "native_importance": model_metadata.get("native_feature_importance", [])[:20],
        "logistic_coefficients": model_metadata.get("coefficients", [])[:20],
    }
    if config.explainability.permutation_importance.get("enabled", False):
        repeats = int(config.explainability.permutation_importance.get("repeats", 20))
        result = permutation_importance(
            model,
            validation_features,
            validation_target,
            n_repeats=repeats,
            random_state=config.experiment.random_seed,
            scoring=config.explainability.permutation_importance.get(
                "scoring", "average_precision"
            ),
            n_jobs=1,
        )
        rows = [
            {
                "feature_name": feature,
                "importance_mean": float(mean),
                "importance_std": float(std),
            }
            for feature, mean, std in zip(
                feature_names,
                result.importances_mean,
                result.importances_std,
                strict=True,
            )
        ]
        global_evidence["permutation_importance"] = sorted(
            rows, key=lambda row: cast(float, row["importance_mean"]), reverse=True
        )[:20]
    return global_evidence


def build_local_explanations(
    *,
    test_features: pd.DataFrame,
    test_target: np.ndarray,
    test_identifiers: pd.DataFrame,
    probabilities: np.ndarray,
    threshold: float,
    feature_evidence: dict[str, Any],
) -> dict[str, Any]:
    predicted = probabilities >= threshold
    candidate_indices = {
        "highest_predicted_risk": int(np.argmax(probabilities)),
        "lowest_predicted_risk": int(np.argmin(probabilities)),
        "near_selected_threshold": int(np.argmin(np.abs(probabilities - threshold))),
    }
    false_positive = np.where((predicted == 1) & (test_target == 0))[0]
    false_negative = np.where((predicted == 0) & (test_target == 1))[0]
    if len(false_positive):
        candidate_indices["false_positive"] = int(false_positive[0])
    if len(false_negative):
        candidate_indices["false_negative"] = int(false_negative[0])
    top_features = [
        item["feature_name"] for item in feature_evidence.get("permutation_importance", [])[:5]
    ]
    examples = []
    seen: set[int] = set()
    for reason, index in candidate_indices.items():
        if index in seen:
            continue
        seen.add(index)
        identifiers = test_identifiers.iloc[index].to_dict()
        examples.append(
            {
                "selection_reason": reason,
                "admission_id": identifiers["admission_id"],
                "patient_id": identifiers["patient_id"],
                "predicted_probability": float(probabilities[index]),
                "predicted_label": bool(predicted[index]),
                "actual_label": bool(test_target[index]),
                "top_feature_values": {
                    feature: float(test_features.iloc[index][feature])
                    for feature in top_features
                    if feature in test_features.columns
                },
            }
        )
    return {
        "method": "deterministic model-agnostic local examples with top global features",
        "non_causal_warning": "Local evidence uses synthetic identifiers only and is not causal.",
        "examples": examples,
    }
