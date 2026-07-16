"""Lineage records for the local governed logical layer."""

from __future__ import annotations

LINEAGE = {
    "curated.patient_admission_view": [
        "raw.patients",
        "raw.admissions",
        "quality.rejected_records",
    ],
    "curated.admission_diagnosis_summary": ["raw.diagnoses", "quality.rejected_records"],
    "curated.daily_ward_operational_context": [
        "raw.ward_capacity",
        "raw.workforce",
        "quality.data_quality_issues",
    ],
    "curated.admission_operational_context": [
        "curated.patient_admission_view",
        "curated.daily_ward_operational_context",
    ],
    "curated.outcome_context_view": ["raw.outcomes", "quality.data_quality_issues"],
    "curated.model_source_view": [
        "curated.patient_admission_view",
        "curated.admission_diagnosis_summary",
        "curated.admission_operational_context",
        "curated.outcome_context_view",
    ],
}


def lineage_for_view(view_name: str) -> list[str]:
    return LINEAGE[view_name]
