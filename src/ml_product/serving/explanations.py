"""Safe concise serving explanations."""

from __future__ import annotations

from typing import Any


def explanation_summary(feature_importance: dict[str, Any]) -> list[str]:
    importance = feature_importance.get("candidate_global_importance", {}).get("xgboost", {})
    rows = importance.get("permutation_importance", [])[:3]
    labels = {
        "initial_news2_score": "higher synthetic acuity score",
        "staff_to_bed_ratio": "staffing context",
        "age": "age",
        "diagnosis_count": "diagnosis burden",
        "comorbidity_count": "comorbidity burden",
    }
    return [labels.get(row["feature_name"], row["feature_name"]) for row in rows]
