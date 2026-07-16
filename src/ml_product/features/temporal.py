"""Admission-time temporal feature derivations."""

from __future__ import annotations

import pandas as pd

SEASONS = {
    12: "winter",
    1: "winter",
    2: "winter",
    3: "spring",
    4: "spring",
    5: "spring",
    6: "summer",
    7: "summer",
    8: "summer",
    9: "autumn",
    10: "autumn",
    11: "autumn",
}


def add_temporal_features(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    admission_datetime = pd.to_datetime(result["admission_datetime"], errors="raise")
    result["admission_hour"] = admission_datetime.dt.hour.astype("int64")
    result["admission_day_of_week"] = admission_datetime.dt.day_name()
    result["weekend_admission"] = admission_datetime.dt.dayofweek.isin([5, 6])
    result["admission_month"] = admission_datetime.dt.month.astype("int64")
    result["admission_season"] = result["admission_month"].map(SEASONS)
    return result
