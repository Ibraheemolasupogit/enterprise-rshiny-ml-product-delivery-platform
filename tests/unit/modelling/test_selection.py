from pathlib import Path

from ml_product.modelling.config import ModelTrainingConfig
from ml_product.modelling.selection import recommend_candidate


def test_selection_uses_validation_rows_only() -> None:
    config = ModelTrainingConfig.from_file(Path("config/model_training.yaml"))
    recommendation = recommend_candidate(
        [
            {
                "model_family": "logistic_regression",
                "recall": 0.9,
                "brier_score": 0.1,
                "pr_auc": 0.8,
            }
        ],
        prevalence_brier=0.2,
        config=config,
    )
    assert recommendation["recommended_model"] == "logistic_regression"
    assert recommendation["recommendation_status"] == "recommended_for_registration_review"
