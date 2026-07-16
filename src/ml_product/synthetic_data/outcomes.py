"""Synthetic admission-outcome source-system generation."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

OUTCOME_COLUMNS = [
    "admission_id",
    "discharge_datetime",
    "length_of_stay_days",
    "long_stay_flag",
    "readmission_30d",
    "discharge_destination",
]

DISCHARGE_DESTINATIONS = [
    "home",
    "home_with_support",
    "community_rehab",
    "care_facility",
    "transfer",
]


def _complexity_score(diagnoses: list[dict[str, Any]]) -> float:
    score_map = {"low": 0.0, "moderate": 1.0, "high": 2.0}
    return max(score_map[row["diagnosis_complexity"]] for row in diagnoses)


def generate_outcomes(
    admissions: list[dict[str, Any]],
    patients_by_id: dict[str, dict[str, Any]],
    diagnoses: list[dict[str, Any]],
    capacity_by_ward_date: dict[tuple[str, str], dict[str, Any]],
    workforce_by_ward_date: dict[tuple[str, str], dict[str, Any]],
    rng: random.Random,
) -> list[dict[str, Any]]:
    diagnoses_by_admission: dict[str, list[dict[str, Any]]] = {}
    for diagnosis in diagnoses:
        diagnoses_by_admission.setdefault(diagnosis["admission_id"], []).append(diagnosis)

    rows: list[dict[str, Any]] = []
    for admission in admissions:
        patient = patients_by_id[admission["patient_id"]]
        admission_dt = datetime.fromisoformat(admission["admission_datetime"])
        record_date = admission_dt.date().isoformat()
        capacity = capacity_by_ward_date[(admission["ward_id"], record_date)]
        workforce = workforce_by_ward_date[(admission["ward_id"], record_date)]
        occupancy_pressure = capacity["occupied_beds"] / capacity["staffed_beds"]
        staffing_pressure = workforce["vacancy_rate"]
        complexity = _complexity_score(diagnoses_by_admission[admission["admission_id"]])
        mobility_adjustment = {
            "independent": 0.0,
            "assisted": 0.8,
            "limited": 1.5,
            "bedbound": 2.3,
        }[admission["mobility_status"]]
        expected_los = (
            2.3
            + patient["age"] / 35
            + patient["comorbidity_count"] * 0.55
            + patient["previous_admissions_12m"] * 0.22
            + admission["initial_news2_score"] * 0.18
            + complexity * 1.15
            + mobility_adjustment
            + max(0.0, occupancy_pressure - 0.86) * 5.0
            + staffing_pressure * 3.0
            + (0.4 if admission_dt.weekday() >= 5 else 0.0)
        )
        length_of_stay_days = max(1, min(28, int(round(rng.gauss(expected_los, 2.2)))))
        discharge_dt = admission_dt + timedelta(days=length_of_stay_days, hours=rng.randint(8, 18))
        readmission_probability = min(
            0.45,
            0.06 + patient["previous_admissions_12m"] * 0.035 + complexity * 0.04,
        )
        rows.append(
            {
                "admission_id": admission["admission_id"],
                "discharge_datetime": discharge_dt.isoformat(timespec="minutes"),
                "length_of_stay_days": length_of_stay_days,
                "long_stay_flag": length_of_stay_days >= 7,
                "readmission_30d": rng.random() < readmission_probability,
                "discharge_destination": rng.choices(
                    DISCHARGE_DESTINATIONS, weights=[56, 20, 12, 8, 4], k=1
                )[0],
            }
        )
    return rows
