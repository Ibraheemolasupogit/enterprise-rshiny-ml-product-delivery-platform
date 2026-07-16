import pandas as pd

from ml_product.features.temporal import add_temporal_features


def test_admission_time_derivations() -> None:
    frame = pd.DataFrame({"admission_datetime": ["2025-01-04T23:15:00"]})
    result = add_temporal_features(frame)
    assert result.loc[0, "admission_hour"] == 23
    assert result.loc[0, "admission_day_of_week"] == "Saturday"
    assert bool(result.loc[0, "weekend_admission"]) is True
    assert result.loc[0, "admission_month"] == 1
    assert result.loc[0, "admission_season"] == "winter"
