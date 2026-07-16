"""Synthetic patient source-system generation."""

from __future__ import annotations

import random
from typing import Any

PATIENT_COLUMNS = [
    "patient_id",
    "age",
    "sex",
    "postcode_region",
    "deprivation_decile",
    "comorbidity_count",
    "previous_admissions_12m",
]

SEX_VALUES = ["female", "male", "not_specified"]
POSTCODE_REGIONS = ["SR-NORTH", "SR-SOUTH", "SR-EAST", "SR-WEST", "SR-CENTRAL"]


def generate_patients(count: int, rng: random.Random) -> list[dict[str, Any]]:
    patients: list[dict[str, Any]] = []
    for index in range(1, count + 1):
        age = min(98, max(18, int(rng.gauss(67, 16))))
        comorbidity_lambda = 0.8 + max(age - 50, 0) / 22
        comorbidity_count = min(8, int(rng.expovariate(1 / comorbidity_lambda)))
        previous_admissions = min(6, int(rng.random() * (1 + comorbidity_count / 1.5)))
        patients.append(
            {
                "patient_id": f"PAT-{index:06d}",
                "age": age,
                "sex": rng.choices(SEX_VALUES, weights=[49, 49, 2], k=1)[0],
                "postcode_region": rng.choice(POSTCODE_REGIONS),
                "deprivation_decile": rng.randint(1, 10),
                "comorbidity_count": comorbidity_count,
                "previous_admissions_12m": previous_admissions,
            }
        )
    return patients
