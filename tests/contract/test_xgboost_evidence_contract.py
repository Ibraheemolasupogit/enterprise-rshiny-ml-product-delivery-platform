import json
from pathlib import Path


def test_xgboost_comparison_and_explainability_evidence_present() -> None:
    comparison = json.loads(
        Path("reports/model_evaluation/model_comparison.json").read_text(encoding="utf-8")
    )
    importance = json.loads(
        Path("reports/model_evaluation/feature_importance.json").read_text(encoding="utf-8")
    )

    xgboost_rows = [row for row in comparison["rows"] if row["model_family"] == "xgboost"]
    assert len(xgboost_rows) == 1
    assert xgboost_rows[0]["candidate_identifier"].startswith("CAND-")
    assert "pr_auc" in xgboost_rows[0]
    assert "brier_score" in xgboost_rows[0]

    xgboost_importance = importance["candidate_global_importance"]["xgboost"]
    assert xgboost_importance["permutation_importance"]
    assert xgboost_importance["native_importance"]
    assert xgboost_importance["small_sample_warning"]
    assert xgboost_importance["non_causal_warning"]
