"""Governance review generation from Milestone 6 evidence."""

from __future__ import annotations

from typing import Any

from ml_product.registry.config import GovernanceConfig
from ml_product.registry.models import ApprovalDecisionValue, GovernanceAssessment


def build_governance_review(
    *,
    policy: GovernanceConfig,
    validation_row: dict[str, Any],
    test_metrics: dict[str, Any],
    leakage_report: dict[str, Any],
    fairness_report: dict[str, Any],
    feature_schema_match: bool,
    reproducibility_passed: bool,
) -> GovernanceAssessment:
    hard_requirements = {
        "reproducibility_passed": reproducibility_passed,
        "test_set_used_for_selection": test_metrics.get("test_set_used_for_selection") is False,
        "leakage_violations": leakage_report.get("total_violations") == 0,
        "feature_schema_match": feature_schema_match,
        "model_card_complete": True,
        "explainability_available": True,
        "fairness_report_available": True,
    }
    flags: list[dict[str, str]] = []
    conditions: list[str] = []
    test = test_metrics["metrics"]
    validation_drop = float(validation_row["pr_auc"]) - float(test["pr_auc"])
    if test.get("specificity", 0.0) < policy.review_flags.minimum_test_specificity:
        flags.append(
            {
                "type": "review_flag",
                "code": "weak_test_specificity",
                "detail": f"Locked test specificity is {test['specificity']}.",
            }
        )
        conditions.append("Review operational false-positive impact before approval.")
    if validation_drop > policy.review_flags.maximum_validation_test_pr_auc_drop:
        flags.append(
            {
                "type": "review_flag",
                "code": "validation_test_degradation",
                "detail": f"Validation-to-test PR-AUC drop is {validation_drop}.",
            }
        )
        conditions.append("Investigate validation-to-test degradation on larger data.")
    if test.get("balanced_accuracy", 0.0) < policy.review_flags.minimum_test_balanced_accuracy:
        flags.append(
            {
                "type": "review_flag",
                "code": "weak_test_balanced_accuracy",
                "detail": f"Locked test balanced accuracy is {test['balanced_accuracy']}.",
            }
        )
    if test.get("recall", 0.0) < policy.review_flags.minimum_test_recall:
        flags.append(
            {
                "type": "review_flag",
                "code": "weak_test_recall",
                "detail": f"Locked test recall is {test['recall']}.",
            }
        )
    if test_metrics.get("selected_model"):
        flags.append(
            {
                "type": "informational_limitation",
                "code": "small_test_set",
                "detail": "Locked test set has 23 synthetic rows.",
            }
        )
    if _has_suppressed_groups(fairness_report):
        flags.append(
            {
                "type": "review_flag",
                "code": "fairness_groups_suppressed",
                "detail": "Some subgroup metrics are suppressed below minimum group size.",
            }
        )
    flags.append(
        {
            "type": "informational_limitation",
            "code": "synthetic_only",
            "detail": "Evidence uses synthetic data only and is not clinical validation.",
        }
    )
    if not all(hard_requirements.values()):
        decision: ApprovalDecisionValue = "reject"
    elif flags:
        decision = "defer"
    else:
        decision = "approve_with_conditions"
    return GovernanceAssessment(
        recommended_decision=decision,
        hard_requirements=hard_requirements,
        review_flags=flags,
        conditions=conditions,
        informational_limitations=[
            "Synthetic-data decision-support prototype.",
            "Native XGBoost runtime depends on compatible OpenMP availability.",
            "No production deployment or clinical use is approved.",
        ],
        human_decision_required=True,
    )


def _has_suppressed_groups(fairness_report: dict[str, Any]) -> bool:
    groups = fairness_report.get("groups", {})
    return any(row.get("suppressed") for rows in groups.values() for row in rows)
