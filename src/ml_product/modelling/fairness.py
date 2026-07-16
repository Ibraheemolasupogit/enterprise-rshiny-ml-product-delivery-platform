"""Exploratory synthetic subgroup performance checks."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ml_product.modelling.evaluation import evaluate_predictions


def build_fairness_report(
    *,
    features: pd.DataFrame,
    target: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
    preprocessor_metadata: dict[str, Any],
    minimum_group_size: int,
) -> dict[str, Any]:
    groups = derive_groups(features, preprocessor_metadata)
    report: dict[str, Any] = {
        "minimum_group_size": minimum_group_size,
        "groups": {},
        "disparities": {},
        "limitations": (
            "Exploratory synthetic subgroup evidence only; small groups are suppressed "
            "and this is not legal, clinical, or fairness certification."
        ),
    }
    for group_name in ("sex", "age_band", "deprivation_group"):
        rows: list[dict[str, Any]] = []
        for value, indices in groups.groupby(group_name).groups.items():
            index_array = np.asarray(list(indices), dtype=int)
            suppressed = len(index_array) < minimum_group_size
            if suppressed:
                rows.append(
                    {
                        "group": str(value),
                        "row_count": int(len(index_array)),
                        "suppressed": True,
                        "suppression_reason": "below minimum group size",
                    }
                )
                continue
            metrics = evaluate_predictions(
                target[index_array],
                probabilities[index_array],
                threshold=threshold,
                prevalence=float(target[index_array].mean()),
            )
            rows.append(
                {
                    "group": str(value),
                    "row_count": int(len(index_array)),
                    "positive_rate": float(target[index_array].mean()),
                    "predicted_positive_rate": metrics["predicted_positive_rate"],
                    "mean_predicted_probability": float(probabilities[index_array].mean()),
                    "recall": metrics["recall"],
                    "specificity": metrics["specificity"],
                    "precision": metrics["precision"],
                    "false_positive_rate": 1 - metrics["specificity"],
                    "false_negative_rate": 1 - metrics["recall"],
                    "brier_score": metrics["brier_score"],
                    "suppressed": False,
                }
            )
        report["groups"][group_name] = rows
        report["disparities"][group_name] = _disparity(rows)
    return report


def derive_groups(features: pd.DataFrame, preprocessor_metadata: dict[str, Any]) -> pd.DataFrame:
    age = _invert_scaled(features["age"], preprocessor_metadata, "age")
    deprivation = _invert_scaled(
        features["deprivation_decile"], preprocessor_metadata, "deprivation_decile"
    )
    return pd.DataFrame(
        {
            "sex": _derive_sex(features),
            "age_band": pd.cut(
                age,
                bins=[-np.inf, 39, 64, 79, np.inf],
                labels=["under_40", "40_to_64", "65_to_79", "80_plus"],
            ).astype(str),
            "deprivation_group": pd.cut(
                deprivation,
                bins=[-np.inf, 3, 7, 10],
                labels=["deciles_1_to_3", "deciles_4_to_7", "deciles_8_to_10"],
            )
            .astype(str)
            .replace("nan", "missing"),
        }
    )


def _invert_scaled(series: pd.Series, metadata: dict[str, Any], column: str) -> pd.Series:
    mean = float(metadata["numeric_means"][column])
    std = float(metadata["numeric_stds"][column])
    return series.astype(float) * std + mean


def _derive_sex(features: pd.DataFrame) -> pd.Series:
    sex_columns = [column for column in features.columns if column.startswith("sex__")]
    labels = []
    for _, row in features[sex_columns].iterrows():
        active = [str(column).replace("sex__", "") for column, value in row.items() if value == 1]
        labels.append(active[0] if active else "missing")
    return pd.Series(labels)


def _disparity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    usable = [row for row in rows if not row.get("suppressed")]
    if len(usable) < 2:
        return {"available": False, "reason": "fewer than two unsuppressed groups"}
    return {
        "available": True,
        "maximum_recall_difference": _spread(usable, "recall"),
        "maximum_false_negative_rate_difference": _spread(usable, "false_negative_rate"),
        "maximum_brier_score_difference": _spread(usable, "brier_score"),
    }


def _spread(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows]
    return float(max(values) - min(values))
