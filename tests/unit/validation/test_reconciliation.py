from ml_product.validation.reconciliation import QUALITY_TREATMENTS, treatment_for_issue


def test_quality_treatments_cover_committed_issue_types() -> None:
    assert treatment_for_issue("orphan_diagnosis") == "quarantine_exclude_curated"
    assert len(QUALITY_TREATMENTS) == 8
