from pathlib import Path

from ml_product.retraining import RetrainingConfig, assess_eligibility


def test_monitoring_review_with_labels_is_eligible() -> None:
    result = assess_eligibility(RetrainingConfig.from_file(Path("config/retraining.yaml")))
    assert result["eligibility_result"] == "eligible"
    assert result["human_initiation_required"] is True
    assert result["drift_alone_is_not_sufficient"] is True


def test_drift_without_labels_is_insufficient_evidence_reason() -> None:
    config = RetrainingConfig.from_file(Path("config/retraining.yaml"))
    result = assess_eligibility(config)
    assert result["label_count"] >= config.eligibility.minimum_labelled_rows
    assert "no_labelled_data" not in result["reasons"]
    assert result["eligibility_result"] == "eligible"
