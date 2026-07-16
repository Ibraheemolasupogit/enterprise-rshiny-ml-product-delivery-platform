from pathlib import Path

import pytest

from ml_product.features.config import FeatureConfig
from ml_product.features.leakage import assert_no_leakage, check_leakage


def test_valid_predictors_pass_leakage() -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    result = check_leakage(config)
    assert result.valid
    assert result.report["total_violations"] == 0


@pytest.mark.parametrize(
    "column",
    [
        "discharge_datetime",
        "length_of_stay_days_governed",
        "readmission_30d",
        "admission_id",
    ],
)
def test_prohibited_predictors_fail(column: str) -> None:
    config = FeatureConfig.from_file(Path("config/features.yaml"))
    payload = config.model_dump(mode="json")
    payload["features"]["numeric"].append(column)
    payload["excluded_predictors"] = [
        item for item in payload["excluded_predictors"] if item != column
    ]
    payload["identifiers"] = ["admission_id", "patient_id"]
    if column == "admission_id":
        with pytest.raises(ValueError, match="Prohibited"):
            FeatureConfig.model_validate(payload)
        return
    mutated = FeatureConfig.model_validate(payload)
    with pytest.raises(ValueError, match="leakage"):
        assert_no_leakage(mutated)
