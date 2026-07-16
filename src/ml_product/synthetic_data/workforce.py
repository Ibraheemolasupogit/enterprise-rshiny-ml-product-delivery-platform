"""Synthetic ward-level workforce source-system generation."""

from __future__ import annotations

import random
from datetime import date
from typing import Any

from ml_product.synthetic_data.admissions import ward_ids
from ml_product.synthetic_data.ward_capacity import date_range

WORKFORCE_COLUMNS = [
    "workforce_record_id",
    "ward_id",
    "record_date",
    "registered_nurses",
    "support_workers",
    "medical_staff",
    "agency_hours",
    "vacancy_rate",
]


def generate_workforce(
    *, ward_count: int, start_date: date, end_date: date, rng: random.Random
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    row_index = 1
    for ward_id in ward_ids(ward_count):
        base_registered = rng.randint(7, 11)
        base_support = rng.randint(5, 9)
        for record_date in date_range(start_date, end_date):
            weekend = record_date.weekday() >= 5
            vacancy_rate = min(0.35, max(0.0, rng.gauss(0.08 + (0.03 if weekend else 0.0), 0.04)))
            rows.append(
                {
                    "workforce_record_id": f"WRK-{row_index:06d}",
                    "ward_id": ward_id,
                    "record_date": record_date.isoformat(),
                    "registered_nurses": max(0, base_registered - int(vacancy_rate * 5)),
                    "support_workers": max(0, base_support - int(vacancy_rate * 4)),
                    "medical_staff": max(1, rng.randint(2, 5) - (1 if weekend else 0)),
                    "agency_hours": round(max(0.0, rng.gauss(5 + vacancy_rate * 30, 3)), 2),
                    "vacancy_rate": round(vacancy_rate, 3),
                }
            )
            row_index += 1
    return rows
