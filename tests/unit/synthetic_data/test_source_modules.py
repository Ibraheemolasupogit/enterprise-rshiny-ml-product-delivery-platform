import random
from datetime import date

from ml_product.synthetic_data.admissions import ADMISSION_COLUMNS, generate_admissions
from ml_product.synthetic_data.diagnoses import DIAGNOSIS_COLUMNS, generate_diagnoses
from ml_product.synthetic_data.outcomes import OUTCOME_COLUMNS
from ml_product.synthetic_data.patients import PATIENT_COLUMNS, generate_patients
from ml_product.synthetic_data.ward_capacity import WARD_CAPACITY_COLUMNS, generate_ward_capacity
from ml_product.synthetic_data.workforce import WORKFORCE_COLUMNS, generate_workforce


def test_patients_schema_and_ranges() -> None:
    rows = generate_patients(10, random.Random(1))

    assert list(rows[0]) == PATIENT_COLUMNS
    assert all(row["patient_id"].startswith("PAT-") for row in rows)
    assert all(18 <= row["age"] <= 98 for row in rows)
    assert all(1 <= row["deprivation_decile"] <= 10 for row in rows)


def test_admissions_schema_and_references() -> None:
    patients = generate_patients(10, random.Random(1))
    rows = generate_admissions(
        patients,
        target_total=12,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        ward_count=2,
        rng=random.Random(2),
    )

    patient_ids = {row["patient_id"] for row in patients}
    assert list(rows[0]) == ADMISSION_COLUMNS
    assert all(row["patient_id"] in patient_ids for row in rows)
    assert all(row["admission_id"].startswith("ADM-") for row in rows)


def test_diagnoses_schema_and_primary_flags() -> None:
    patients = generate_patients(10, random.Random(1))
    admissions = generate_admissions(
        patients,
        target_total=12,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        ward_count=2,
        rng=random.Random(2),
    )
    rows = generate_diagnoses(
        admissions, minimum_per_admission=1, maximum_per_admission=3, rng=random.Random(3)
    )

    assert list(rows[0]) == DIAGNOSIS_COLUMNS
    for admission in admissions:
        assert (
            sum(
                row["admission_id"] == admission["admission_id"] and row["primary_diagnosis_flag"]
                for row in rows
            )
            == 1
        )


def test_capacity_and_workforce_daily_rows() -> None:
    capacity = generate_ward_capacity(
        ward_count=2, start_date=date(2025, 1, 1), end_date=date(2025, 1, 3), rng=random.Random(4)
    )
    workforce = generate_workforce(
        ward_count=2, start_date=date(2025, 1, 1), end_date=date(2025, 1, 3), rng=random.Random(5)
    )

    assert list(capacity[0]) == WARD_CAPACITY_COLUMNS
    assert list(workforce[0]) == WORKFORCE_COLUMNS
    assert len(capacity) == 6
    assert len(workforce) == 6
    assert OUTCOME_COLUMNS[0] == "admission_id"
