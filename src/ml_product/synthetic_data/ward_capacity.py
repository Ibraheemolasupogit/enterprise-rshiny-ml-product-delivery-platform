"""Synthetic ward-capacity source-system generation."""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Any

from ml_product.synthetic_data.admissions import ward_ids

WARD_CAPACITY_COLUMNS = [
    "ward_id",
    "record_date",
    "staffed_beds",
    "occupied_beds",
    "closed_beds",
    "isolation_capacity",
]


def date_range(start_date: date, end_date: date) -> list[date]:
    return [
        start_date + timedelta(days=offset) for offset in range((end_date - start_date).days + 1)
    ]


def generate_ward_capacity(
    *, ward_count: int, start_date: date, end_date: date, rng: random.Random
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ward_id in ward_ids(ward_count):
        base_beds = rng.randint(20, 34)
        for record_date in date_range(start_date, end_date):
            closed_beds = rng.choices([0, 1, 2, 3], weights=[70, 18, 9, 3], k=1)[0]
            staffed_beds = max(1, base_beds - closed_beds)
            weekday_pressure = 0.05 if record_date.weekday() in {0, 1, 2} else -0.02
            occupancy_rate = min(0.98, max(0.55, rng.gauss(0.84 + weekday_pressure, 0.08)))
            rows.append(
                {
                    "ward_id": ward_id,
                    "record_date": record_date.isoformat(),
                    "staffed_beds": staffed_beds,
                    "occupied_beds": min(staffed_beds, int(round(staffed_beds * occupancy_rate))),
                    "closed_beds": closed_beds,
                    "isolation_capacity": rng.randint(1, 5),
                }
            )
    return rows
