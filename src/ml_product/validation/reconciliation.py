"""Quality-fixture reconciliation rules."""

from __future__ import annotations

QUALITY_TREATMENTS = {
    "missing_deprivation_decile": "preserve_with_quality_flag",
    "missing_mobility_status": "preserve_with_quality_flag",
    "duplicate_patient": "quarantine_duplicate_exclude_curated",
    "duplicate_admission": "quarantine_duplicate_exclude_curated",
    "orphan_diagnosis": "quarantine_exclude_curated",
    "inconsistent_long_stay_flag": "preserve_source_and_governed_recalculate",
    "occupied_beds_over_capacity": "accepted_operational_exception",
    "vacancy_rate_out_of_range": "quarantine_metric_exclude_curated_metric",
}


def treatment_for_issue(issue_type: str) -> str:
    return QUALITY_TREATMENTS[issue_type]
