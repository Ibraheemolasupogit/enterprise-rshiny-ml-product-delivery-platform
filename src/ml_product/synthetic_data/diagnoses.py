"""Synthetic broad diagnosis source-system generation."""

from __future__ import annotations

import random
from typing import Any

DIAGNOSIS_COLUMNS = [
    "diagnosis_id",
    "admission_id",
    "diagnosis_group",
    "diagnosis_complexity",
    "primary_diagnosis_flag",
]

DIAGNOSIS_GROUPS = [
    "respiratory_synthetic",
    "cardiovascular_synthetic",
    "frailty_synthetic",
    "infection_synthetic",
    "surgical_synthetic",
    "other_synthetic",
]
DIAGNOSIS_COMPLEXITIES = ["low", "moderate", "high"]


def generate_diagnoses(
    admissions: list[dict[str, Any]],
    *,
    minimum_per_admission: int,
    maximum_per_admission: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    diagnoses: list[dict[str, Any]] = []
    diagnosis_index = 1
    for admission in admissions:
        diagnosis_count = rng.randint(minimum_per_admission, maximum_per_admission)
        for sequence in range(diagnosis_count):
            diagnoses.append(
                {
                    "diagnosis_id": f"DIA-{diagnosis_index:06d}",
                    "admission_id": admission["admission_id"],
                    "diagnosis_group": rng.choice(DIAGNOSIS_GROUPS),
                    "diagnosis_complexity": rng.choices(
                        DIAGNOSIS_COMPLEXITIES, weights=[42, 40, 18], k=1
                    )[0],
                    "primary_diagnosis_flag": sequence == 0,
                }
            )
            diagnosis_index += 1
    return diagnoses
