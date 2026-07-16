import json
from pathlib import Path


def _load(name: str) -> dict:
    return json.loads((Path("reports/retraining") / name).read_text(encoding="utf-8"))


def test_champion_is_registered_comparison_model_not_active_model() -> None:
    champion = _load("champion_metrics.json")
    assert champion["candidate_identifier"] == "CAND-85EA9202CAD6FE7F"
    assert champion["registry_version"] == 1
    assert champion["registry_state"] == "registered"
    assert champion["approval_state"] == "pending"
    assert champion["activation_state"] == "inactive"
    assert champion["refit_performed"] is False


def test_comparison_metric_directions_and_deltas() -> None:
    comparison = _load("champion_challenger_comparison.json")
    row = comparison["challengers"][0]
    assert comparison["same_row_evaluation_confirmation"] is True
    assert comparison["historical_test_set_used_for_selection"] is False
    assert row["metric_directions"]["pr_auc"] == "higher_is_better"
    assert row["metric_directions"]["brier_score"] == "lower_is_better"
    assert "challenger_minus_champion_pr_auc" in row
    assert "challenger_minus_champion_weighted_cost" in row


def test_gates_do_not_imply_approval() -> None:
    gates = _load("promotion_gates.json")
    assert gates["approval_not_implied"] is True
    assert gates["hard_gates"]["historical_test_not_used"] is True
    assert gates["overall_result"] in {"pass", "conditional", "fail", "insufficient_evidence"}


def test_recommendation_retains_model_lifecycle_boundaries() -> None:
    recommendation = _load("retraining_recommendation.json")
    assert recommendation["recommendation"] in {
        "recommend_challenger_for_registration_review",
        "retain_champion",
        "reject_challenger",
        "defer_retraining",
        "insufficient_evidence",
    }
    assert recommendation["approval_status"] == "not_granted"
    assert recommendation["activation_status"] == "inactive"
    assert recommendation["deployment_status"] == "not_performed"
    assert recommendation["automatic_action"] == "none"
