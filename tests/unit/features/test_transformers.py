from pathlib import Path

import pandas as pd

from ml_product.features.config import FeatureConfig
from ml_product.features.transformers import fit_preprocessor


def test_preprocessor_fits_training_only_and_ignores_unknown_categories() -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    train = _minimal_frame(["A", "B"], [1.0, None])
    validation = _minimal_frame(["C"], [100.0])
    preprocessor = fit_preprocessor(train, config)
    transformed = preprocessor.transform(validation, config)
    assert "sex__c" not in transformed.columns
    assert preprocessor.numeric_medians["age"] == 1.0
    assert preprocessor.metadata["not_a_predictive_model"] is True
    assert transformed.isna().sum().sum() == 0


def _minimal_frame(sexes: list[str], ages: list[float | None]) -> pd.DataFrame:
    rows = len(sexes)
    data = {
        "age": ages,
        "deprivation_decile": [5] * rows,
        "comorbidity_count": [1] * rows,
        "previous_admissions_12m": [0] * rows,
        "initial_news2_score": [2] * rows,
        "diagnosis_count": [1] * rows,
        "secondary_diagnosis_count": [0] * rows,
        "occupancy_rate": [0.8] * rows,
        "staff_to_bed_ratio": [0.4] * rows,
        "admission_hour": [10] * rows,
        "admission_month": [1] * rows,
        "weekend_admission": [False] * rows,
        "sex": sexes,
        "postcode_region": ["North"] * rows,
        "admission_type": ["Emergency"] * rows,
        "source_of_admission": ["Home"] * rows,
        "mobility_status": ["Independent"] * rows,
        "primary_diagnosis_group": ["Respiratory"] * rows,
        "primary_diagnosis_complexity": ["medium"] * rows,
        "admission_day_of_week": ["Monday"] * rows,
        "admission_season": ["winter"] * rows,
    }
    return pd.DataFrame(data)
