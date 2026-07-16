import json
from pathlib import Path


def test_model_metrics_contract() -> None:
    validation = json.loads(
        Path("reports/model_evaluation/validation_metrics.json").read_text(encoding="utf-8")
    )
    test = json.loads(
        Path("reports/model_evaluation/test_metrics.json").read_text(encoding="utf-8")
    )
    assert validation["rows"]
    families = {row["model_family"] for row in validation["rows"]}
    assert {
        "baseline_prevalence",
        "baseline_majority_class",
        "logistic_regression",
        "random_forest",
        "xgboost",
    }.issubset(families)
    assert test["test_set_used_for_selection"] is False
    assert "brier_score" in test["metrics"]
    assert "pr_auc" in test["metrics"]
