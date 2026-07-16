"""Apply the registered Milestone 5 preprocessing contract to raw API inputs."""

from __future__ import annotations

from typing import Any, cast

import pandas as pd

from ml_product.serving.schemas import PredictionRequest

NUMERIC_FIELDS = [
    "age",
    "deprivation_decile",
    "comorbidity_count",
    "previous_admissions_12m",
    "initial_news2_score",
    "diagnosis_count",
    "secondary_diagnosis_count",
    "occupancy_rate",
    "staff_to_bed_ratio",
    "admission_hour",
    "admission_month",
]
CATEGORICAL_FIELDS = [
    "sex",
    "postcode_region",
    "admission_type",
    "source_of_admission",
    "mobility_status",
    "primary_diagnosis_group",
    "primary_diagnosis_complexity",
    "admission_day_of_week",
    "admission_season",
]


def transform_request(request: PredictionRequest, metadata: dict[str, Any]) -> pd.DataFrame:
    raw = request.model_dump()
    admission = request.admission_datetime
    occupancy_rate = request.occupancy_rate
    if occupancy_rate is None:
        occupancy_rate = request.occupied_beds / request.staffed_beds
    staff_to_bed_ratio = request.staff_to_bed_ratio
    if staff_to_bed_ratio is None:
        staff_to_bed_ratio = (
            request.registered_nurses + request.support_workers + request.medical_staff
        ) / request.staffed_beds
    source = {
        **raw,
        "occupancy_rate": occupancy_rate,
        "staff_to_bed_ratio": staff_to_bed_ratio,
        "admission_hour": float(admission.hour),
        "admission_month": float(admission.month),
        "weekend_admission": admission.weekday() >= 5,
        "admission_day_of_week": admission.strftime("%A"),
        "admission_season": _season(admission.month),
    }
    output: dict[str, float] = {}
    for feature in metadata["output_feature_names"]:
        if feature.endswith("__missing"):
            source_name = feature[: -len("__missing")]
            output[feature] = 1.0 if source.get(source_name) is None else 0.0
        elif feature in NUMERIC_FIELDS or feature in {"weekend_admission"}:
            output[feature] = _scale_numeric(feature, source.get(feature), metadata)
        elif "__" in feature:
            source_name, level = feature.split("__", 1)
            output[feature] = _encode_category(source_name, level, source.get(source_name))
        else:
            output[feature] = 0.0
    return pd.DataFrame([output], columns=metadata["output_feature_names"])


def _scale_numeric(name: str, value: object, metadata: dict[str, Any]) -> float:
    if name == "weekend_admission":
        return float(bool(value))
    if value is None:
        numeric_value = float(metadata["numeric_medians"].get(name, 0.0))
    else:
        numeric_value = float(cast(float | int | str, value))
    mean = float(metadata["numeric_means"][name])
    std = float(metadata["numeric_stds"][name]) or 1.0
    return (float(numeric_value) - mean) / std


def _encode_category(name: str, level: str, value: object) -> float:
    if value is None:
        observed = "__missing__"
    else:
        observed = str(value).lower().replace("-", "_")
    return 1.0 if observed == level else 0.0


def _season(month: int) -> str:
    if month in {3, 4, 5}:
        return "spring"
    if month in {6, 7, 8}:
        return "summer"
    if month in {9, 10, 11}:
        return "autumn"
    return "winter"
