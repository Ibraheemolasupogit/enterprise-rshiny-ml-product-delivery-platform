"""Controlled deterministic data-quality fixture injection."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DataQualityIssue:
    issue_id: str
    dataset: str
    issue_type: str
    record_identifier: str
    column: str
    expected_rule: str
    injected_value_summary: str
    seed: int
    intentional: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id,
            "dataset": self.dataset,
            "issue_type": self.issue_type,
            "record_identifier": self.record_identifier,
            "column": self.column,
            "expected_rule": self.expected_rule,
            "injected_value_summary": self.injected_value_summary,
            "seed": self.seed,
            "intentional": self.intentional,
        }


def _issue_count(rate: float, row_count: int) -> int:
    if rate <= 0 or row_count == 0:
        return 0
    return max(1, min(row_count, round(rate * row_count)))


def _sample_indices(rng: random.Random, row_count: int, count: int) -> list[int]:
    return sorted(rng.sample(range(row_count), k=min(count, row_count)))


def _append_issue(
    issues: list[DataQualityIssue],
    *,
    dataset: str,
    issue_type: str,
    record_identifier: str,
    column: str,
    expected_rule: str,
    injected_value_summary: str,
    seed: int,
) -> None:
    issues.append(
        DataQualityIssue(
            issue_id=f"DQ-{len(issues) + 1:06d}",
            dataset=dataset,
            issue_type=issue_type,
            record_identifier=record_identifier,
            column=column,
            expected_rule=expected_rule,
            injected_value_summary=injected_value_summary,
            seed=seed,
        )
    )


def apply_quality_issues(
    tables: dict[str, list[dict[str, Any]]],
    rates: dict[str, float],
    *,
    seed: int,
) -> list[dict[str, Any]]:
    """Apply configured intentional fixtures and return issue manifest rows."""

    rng = random.Random(seed + 9901)
    issues: list[DataQualityIssue] = []

    patients = tables["patients"]
    for idx in _sample_indices(
        rng, len(patients), _issue_count(rates.get("missing_deprivation_decile", 0), len(patients))
    ):
        patients[idx]["deprivation_decile"] = None
        _append_issue(
            issues,
            dataset="patients",
            issue_type="missing_deprivation_decile",
            record_identifier=patients[idx]["patient_id"],
            column="deprivation_decile",
            expected_rule="deprivation_decile is normally an integer from 1 to 10",
            injected_value_summary="null",
            seed=seed,
        )

    duplicate_count = _issue_count(rates.get("duplicate_patient", 0), len(patients))
    for idx in _sample_indices(rng, len(patients), duplicate_count):
        patients.append(dict(patients[idx]))
        _append_issue(
            issues,
            dataset="patients",
            issue_type="duplicate_patient",
            record_identifier=patients[idx]["patient_id"],
            column="patient_id",
            expected_rule="patient_id is unique in clean data",
            injected_value_summary="duplicate row appended",
            seed=seed,
        )

    admissions = tables["admissions"]
    for idx in _sample_indices(
        rng, len(admissions), _issue_count(rates.get("missing_mobility_status", 0), len(admissions))
    ):
        admissions[idx]["mobility_status"] = None
        _append_issue(
            issues,
            dataset="admissions",
            issue_type="missing_mobility_status",
            record_identifier=admissions[idx]["admission_id"],
            column="mobility_status",
            expected_rule="mobility_status uses the controlled vocabulary",
            injected_value_summary="null",
            seed=seed,
        )

    for idx in _sample_indices(
        rng, len(admissions), _issue_count(rates.get("duplicate_admission", 0), len(admissions))
    ):
        admissions.append(dict(admissions[idx]))
        _append_issue(
            issues,
            dataset="admissions",
            issue_type="duplicate_admission",
            record_identifier=admissions[idx]["admission_id"],
            column="admission_id",
            expected_rule="admission_id is unique in clean data",
            injected_value_summary="duplicate row appended",
            seed=seed,
        )

    diagnoses = tables["diagnoses"]
    for idx in _sample_indices(
        rng, len(diagnoses), _issue_count(rates.get("orphan_diagnosis", 0), len(admissions))
    ):
        diagnoses[idx]["admission_id"] = "ADM-999999"
        _append_issue(
            issues,
            dataset="diagnoses",
            issue_type="orphan_diagnosis",
            record_identifier=diagnoses[idx]["diagnosis_id"],
            column="admission_id",
            expected_rule="diagnosis admission_id references admissions.admission_id",
            injected_value_summary="ADM-999999",
            seed=seed,
        )

    outcomes = tables["outcomes"]
    for idx in _sample_indices(
        rng,
        len(outcomes),
        _issue_count(rates.get("inconsistent_long_stay_flag", 0), len(outcomes)),
    ):
        outcomes[idx]["long_stay_flag"] = not outcomes[idx]["long_stay_flag"]
        _append_issue(
            issues,
            dataset="outcomes",
            issue_type="inconsistent_long_stay_flag",
            record_identifier=outcomes[idx]["admission_id"],
            column="long_stay_flag",
            expected_rule="long_stay_flag equals length_of_stay_days >= 7",
            injected_value_summary=str(outcomes[idx]["long_stay_flag"]).lower(),
            seed=seed,
        )

    capacity = tables["ward_capacity"]
    for idx in _sample_indices(
        rng,
        len(capacity),
        _issue_count(rates.get("occupied_beds_over_capacity", 0), len(capacity)),
    ):
        capacity[idx]["occupied_beds"] = capacity[idx]["staffed_beds"] + 2
        _append_issue(
            issues,
            dataset="ward_capacity",
            issue_type="occupied_beds_over_capacity",
            record_identifier=f"{capacity[idx]['ward_id']}|{capacity[idx]['record_date']}",
            column="occupied_beds",
            expected_rule="occupied_beds normally does not exceed staffed_beds",
            injected_value_summary=str(capacity[idx]["occupied_beds"]),
            seed=seed,
        )

    workforce = tables["workforce"]
    for idx in _sample_indices(
        rng,
        len(workforce),
        _issue_count(rates.get("vacancy_rate_out_of_range", 0), len(workforce)),
    ):
        workforce[idx]["vacancy_rate"] = 1.25
        _append_issue(
            issues,
            dataset="workforce",
            issue_type="vacancy_rate_out_of_range",
            record_identifier=workforce[idx]["workforce_record_id"],
            column="vacancy_rate",
            expected_rule="vacancy_rate normally remains between 0.0 and 1.0",
            injected_value_summary="1.25",
            seed=seed,
        )

    return [issue.as_dict() for issue in issues]
