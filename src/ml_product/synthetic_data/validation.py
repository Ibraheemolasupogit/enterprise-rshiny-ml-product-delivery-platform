"""Validation for synthetic source datasets."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pandas as pd

from ml_product.synthetic_data.admissions import (
    ADMISSION_COLUMNS,
    ADMISSION_TYPES,
    MOBILITY_STATUSES,
)
from ml_product.synthetic_data.diagnoses import (
    DIAGNOSIS_COLUMNS,
    DIAGNOSIS_COMPLEXITIES,
    DIAGNOSIS_GROUPS,
)
from ml_product.synthetic_data.outcomes import DISCHARGE_DESTINATIONS, OUTCOME_COLUMNS
from ml_product.synthetic_data.patients import PATIENT_COLUMNS, POSTCODE_REGIONS, SEX_VALUES
from ml_product.synthetic_data.ward_capacity import WARD_CAPACITY_COLUMNS
from ml_product.synthetic_data.workforce import WORKFORCE_COLUMNS

DATASET_COLUMNS = {
    "patients": PATIENT_COLUMNS,
    "admissions": ADMISSION_COLUMNS,
    "diagnoses": DIAGNOSIS_COLUMNS,
    "ward_capacity": WARD_CAPACITY_COLUMNS,
    "workforce": WORKFORCE_COLUMNS,
    "outcomes": OUTCOME_COLUMNS,
}

PRIMARY_KEYS = {
    "patients": ["patient_id"],
    "admissions": ["admission_id"],
    "diagnoses": ["diagnosis_id"],
    "ward_capacity": ["ward_id", "record_date"],
    "workforce": ["workforce_record_id"],
    "outcomes": ["admission_id"],
}

ISSUE_ALLOWANCES = {
    "patients": {"duplicate_patient", "missing_deprivation_decile"},
    "admissions": {"duplicate_admission", "missing_mobility_status", "unknown_patient"},
    "diagnoses": {"orphan_diagnosis", "multiple_primary_diagnoses", "no_primary_diagnosis"},
    "ward_capacity": {"occupied_beds_over_capacity"},
    "workforce": {"vacancy_rate_out_of_range", "missing_workforce_count"},
    "outcomes": {"orphan_outcome", "discharge_before_admission", "inconsistent_long_stay_flag"},
}


def issue_counter(issues: list[dict[str, Any]]) -> Counter[tuple[str, str]]:
    return Counter((issue["dataset"], issue["issue_type"]) for issue in issues)


def _unexpected(
    errors: list[str],
    issues: list[dict[str, Any]],
    *,
    dataset: str,
    issue_type: str,
    message: str,
) -> None:
    if (dataset, issue_type) not in issue_counter(issues):
        errors.append(message)


def validate_tables(
    tables: dict[str, list[dict[str, Any]]],
    issues: list[dict[str, Any]] | None = None,
) -> list[str]:
    issues = issues or []
    errors: list[str] = []

    for dataset, columns in DATASET_COLUMNS.items():
        if dataset not in tables:
            errors.append(f"Missing dataset: {dataset}")
            continue
        for row_index, row in enumerate(tables[dataset], start=1):
            if list(row) != columns:
                errors.append(f"{dataset} row {row_index} has unstable columns")

    patients = tables.get("patients", [])
    admissions = tables.get("admissions", [])
    diagnoses = tables.get("diagnoses", [])
    capacity = tables.get("ward_capacity", [])
    workforce = tables.get("workforce", [])
    outcomes = tables.get("outcomes", [])

    patient_ids = {row["patient_id"] for row in patients}
    admission_ids = {row["admission_id"] for row in admissions}
    ward_ids = {row["ward_id"] for row in capacity}

    for dataset, keys in PRIMARY_KEYS.items():
        values = [tuple(row[key] for key in keys) for row in tables.get(dataset, [])]
        if len(values) != len(set(values)):
            issue_type = (
                f"duplicate_{dataset[:-1]}" if dataset.endswith("s") else f"duplicate_{dataset}"
            )
            _unexpected(
                errors,
                issues,
                dataset=dataset,
                issue_type=issue_type,
                message=f"{dataset} has duplicate primary keys",
            )

    for row in patients:
        if not 18 <= int(row["age"]) <= 98:
            errors.append("patients.age outside synthetic range")
        if row["sex"] not in SEX_VALUES:
            errors.append("patients.sex outside controlled vocabulary")
        if row["postcode_region"] not in POSTCODE_REGIONS:
            errors.append("patients.postcode_region outside controlled vocabulary")
        if row["deprivation_decile"] is None:
            _unexpected(
                errors,
                issues,
                dataset="patients",
                issue_type="missing_deprivation_decile",
                message="patients.deprivation_decile is unexpectedly missing",
            )
        elif not 1 <= int(row["deprivation_decile"]) <= 10:
            errors.append("patients.deprivation_decile outside 1..10")

    for row in admissions:
        if row["patient_id"] not in patient_ids:
            _unexpected(
                errors,
                issues,
                dataset="admissions",
                issue_type="unknown_patient",
                message="admission references unknown patient",
            )
        if row["admission_type"] not in ADMISSION_TYPES:
            errors.append("admissions.admission_type outside controlled vocabulary")
        if row["mobility_status"] is None:
            _unexpected(
                errors,
                issues,
                dataset="admissions",
                issue_type="missing_mobility_status",
                message="admissions.mobility_status unexpectedly missing",
            )
        elif row["mobility_status"] not in MOBILITY_STATUSES:
            errors.append("admissions.mobility_status outside controlled vocabulary")
        if row["ward_id"] not in ward_ids:
            errors.append("admissions.ward_id references unknown ward")
        if not 0 <= int(row["initial_news2_score"]) <= 20:
            errors.append("admissions.initial_news2_score outside 0..20")

    diagnosis_primary_counts: Counter[str] = Counter()
    for row in diagnoses:
        if row["admission_id"] not in admission_ids:
            _unexpected(
                errors,
                issues,
                dataset="diagnoses",
                issue_type="orphan_diagnosis",
                message="diagnosis references unknown admission",
            )
        if row["diagnosis_group"] not in DIAGNOSIS_GROUPS:
            errors.append("diagnoses.diagnosis_group outside controlled vocabulary")
        if row["diagnosis_complexity"] not in DIAGNOSIS_COMPLEXITIES:
            errors.append("diagnoses.diagnosis_complexity outside controlled vocabulary")
        if bool(row["primary_diagnosis_flag"]):
            diagnosis_primary_counts[row["admission_id"]] += 1
    for admission_id in admission_ids:
        if diagnosis_primary_counts[admission_id] != 1:
            errors.append(f"admission {admission_id} does not have exactly one primary diagnosis")

    for row in capacity:
        if int(row["staffed_beds"]) <= 0:
            errors.append("ward_capacity.staffed_beds must be positive")
        if int(row["occupied_beds"]) > int(row["staffed_beds"]):
            _unexpected(
                errors,
                issues,
                dataset="ward_capacity",
                issue_type="occupied_beds_over_capacity",
                message="occupied beds unexpectedly exceed staffed beds",
            )
        if int(row["closed_beds"]) < 0 or int(row["isolation_capacity"]) < 0:
            errors.append("ward_capacity has negative capacity values")

    for row in workforce:
        if row["ward_id"] not in ward_ids:
            errors.append("workforce.ward_id references unknown ward")
        for column in ("registered_nurses", "support_workers", "medical_staff"):
            if row[column] is None:
                _unexpected(
                    errors,
                    issues,
                    dataset="workforce",
                    issue_type="missing_workforce_count",
                    message="workforce count unexpectedly missing",
                )
            elif int(row[column]) < 0:
                errors.append(f"workforce.{column} is negative")
        if float(row["agency_hours"]) < 0:
            errors.append("workforce.agency_hours is negative")
        if not 0.0 <= float(row["vacancy_rate"]) <= 1.0:
            _unexpected(
                errors,
                issues,
                dataset="workforce",
                issue_type="vacancy_rate_out_of_range",
                message="workforce.vacancy_rate unexpectedly outside 0..1",
            )

    admissions_by_id = {row["admission_id"]: row for row in admissions}
    for row in outcomes:
        admission = admissions_by_id.get(row["admission_id"])
        if admission is None:
            _unexpected(
                errors,
                issues,
                dataset="outcomes",
                issue_type="orphan_outcome",
                message="outcome references unknown admission",
            )
            continue
        admission_dt = datetime.fromisoformat(admission["admission_datetime"])
        discharge_dt = datetime.fromisoformat(row["discharge_datetime"])
        if discharge_dt <= admission_dt:
            _unexpected(
                errors,
                issues,
                dataset="outcomes",
                issue_type="discharge_before_admission",
                message="discharge precedes admission",
            )
        if int(row["length_of_stay_days"]) < 1:
            errors.append("outcomes.length_of_stay_days must be positive")
        if bool(row["long_stay_flag"]) != (int(row["length_of_stay_days"]) >= 7):
            _unexpected(
                errors,
                issues,
                dataset="outcomes",
                issue_type="inconsistent_long_stay_flag",
                message="long_stay_flag inconsistent",
            )
        if row["discharge_destination"] not in DISCHARGE_DESTINATIONS:
            errors.append("outcomes.discharge_destination outside controlled vocabulary")

    invalid_issue_types = [
        issue["issue_type"]
        for issue in issues
        if issue["issue_type"] not in ISSUE_ALLOWANCES.get(issue["dataset"], set())
    ]
    if invalid_issue_types:
        errors.append(f"unsupported issue types: {sorted(set(invalid_issue_types))}")
    return errors


def load_tables_from_directory(directory: Path) -> dict[str, list[dict[str, Any]]]:
    tables: dict[str, list[dict[str, Any]]] = {}
    for dataset, columns in DATASET_COLUMNS.items():
        path = directory / f"{dataset}.csv"
        frame = pd.read_csv(path, keep_default_na=False, na_values=[""])
        rows = cast(list[dict[Any, Any]], frame[columns].to_dict(orient="records"))
        tables[dataset] = [
            {str(key): None if pd.isna(value) else value for key, value in row.items()}
            for row in rows
        ]
    return tables
