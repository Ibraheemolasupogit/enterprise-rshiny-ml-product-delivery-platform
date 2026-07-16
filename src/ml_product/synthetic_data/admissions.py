"""Synthetic admissions source-system generation."""

from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta
from typing import Any

ADMISSION_COLUMNS = [
    "admission_id",
    "patient_id",
    "admission_datetime",
    "admission_type",
    "source_of_admission",
    "ward_id",
    "initial_news2_score",
    "mobility_status",
]

ADMISSION_TYPES = ["emergency", "urgent", "planned"]
SOURCES_OF_ADMISSION = ["home", "clinic", "transfer", "care_facility"]
MOBILITY_STATUSES = ["independent", "assisted", "limited", "bedbound"]


def ward_ids(ward_count: int) -> list[str]:
    return [f"WARD-{index:02d}" for index in range(1, ward_count + 1)]


def _random_datetime(start_date: date, end_date: date, rng: random.Random) -> datetime:
    days = (end_date - start_date).days
    selected = start_date + timedelta(days=rng.randint(0, days))
    selected_time = time(hour=rng.randint(0, 23), minute=rng.choice([0, 15, 30, 45]))
    return datetime.combine(selected, selected_time)


def generate_admissions(
    patients: list[dict[str, Any]],
    *,
    target_total: int,
    start_date: date,
    end_date: date,
    ward_count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    weighted_patients = sorted(
        patients,
        key=lambda row: (
            row["previous_admissions_12m"] + row["comorbidity_count"] + rng.random(),
            row["patient_id"],
        ),
        reverse=True,
    )
    wards = ward_ids(ward_count)
    admissions: list[dict[str, Any]] = []
    for index in range(1, target_total + 1):
        patient = weighted_patients[(index - 1) % len(weighted_patients)]
        admission_type = rng.choices(ADMISSION_TYPES, weights=[62, 23, 15], k=1)[0]
        news_mean = {"emergency": 4.5, "urgent": 3.0, "planned": 1.5}[admission_type]
        news2 = min(20, max(0, int(rng.gauss(news_mean + patient["comorbidity_count"] * 0.35, 2))))
        admissions.append(
            {
                "admission_id": f"ADM-{index:06d}",
                "patient_id": patient["patient_id"],
                "admission_datetime": _random_datetime(start_date, end_date, rng).isoformat(
                    timespec="minutes"
                ),
                "admission_type": admission_type,
                "source_of_admission": rng.choices(
                    SOURCES_OF_ADMISSION, weights=[58, 18, 15, 9], k=1
                )[0],
                "ward_id": rng.choice(wards),
                "initial_news2_score": news2,
                "mobility_status": rng.choices(MOBILITY_STATUSES, weights=[42, 32, 20, 6], k=1)[0],
            }
        )
    return sorted(admissions, key=lambda row: row["admission_id"])
