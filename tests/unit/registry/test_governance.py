import json
from pathlib import Path

from ml_product.registry.config import GovernanceConfig
from ml_product.registry.governance import build_governance_review


def test_governance_surfaces_weak_specificity_and_defers() -> None:
    policy = GovernanceConfig.from_file(Path("config/model_governance.yaml"))
    validation = json.loads(
        Path("reports/model_evaluation/validation_metrics.json").read_text(encoding="utf-8")
    )
    test = json.loads(
        Path("reports/model_evaluation/test_metrics.json").read_text(encoding="utf-8")
    )
    leakage = json.loads(
        Path("reports/model_evaluation/leakage_report.json").read_text(encoding="utf-8")
    )
    fairness = json.loads(
        Path("reports/model_evaluation/fairness_report.json").read_text(encoding="utf-8")
    )
    row = next(item for item in validation["rows"] if item["model_family"] == "xgboost")
    review = build_governance_review(
        policy=policy,
        validation_row=row,
        test_metrics=test,
        leakage_report=leakage,
        fairness_report=fairness,
        feature_schema_match=True,
        reproducibility_passed=True,
    )
    assert review.recommended_decision == "defer"
    assert any(flag["code"] == "weak_test_specificity" for flag in review.review_flags)
    assert review.human_decision_required is True
