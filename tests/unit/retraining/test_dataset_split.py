import json
from pathlib import Path


def _load(name: str) -> dict:
    return json.loads((Path("reports/retraining") / name).read_text(encoding="utf-8"))


def test_dataset_manifest_excludes_unsafe_predictors() -> None:
    manifest = _load("retraining_dataset_manifest.json")
    assert manifest["identifier_columns_excluded_from_predictors"] is True
    assert manifest["outcome_fields_excluded_from_predictors"] is True
    assert manifest["historical_test_rows_used"] == 0
    assert manifest["synthetic_data_declaration"].startswith("Synthetic")


def test_split_preserves_group_and_temporal_boundaries() -> None:
    split = _load("retraining_split_summary.json")
    assert split["patient_overlap_count"] == 0
    assert split["admission_overlap_count"] == 0
    assert split["temporal_split"] is True
    assert split["historical_test_set_touched"] is False
    assert split["train_rows"] > 0
    assert split["validation_rows"] > 0


def test_preprocessing_fits_on_train_only() -> None:
    metadata = _load("retraining_preprocessor_metadata.json")
    assert metadata["fit_on_retraining_train_only"] is True
    assert metadata["validation_transformed_with_training_state"] is True
    assert metadata["reused_old_fitted_preprocessor"] is False
    assert metadata["feature_schema_matches_champion"] is True
