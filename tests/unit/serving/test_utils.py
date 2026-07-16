from typing import Any


def sample_request_payload() -> dict[str, Any]:
    return {
        "age": 72,
        "sex": "male",
        "postcode_region": "SR-EAST",
        "deprivation_decile": 3,
        "comorbidity_count": 2,
        "previous_admissions_12m": 1,
        "admission_type": "emergency",
        "source_of_admission": "home",
        "initial_news2_score": 6,
        "mobility_status": "assisted",
        "primary_diagnosis_group": "respiratory_synthetic",
        "primary_diagnosis_complexity": "moderate",
        "diagnosis_count": 3,
        "secondary_diagnosis_count": 2,
        "staffed_beds": 30,
        "occupied_beds": 27,
        "closed_beds": 1,
        "isolation_capacity": 2,
        "registered_nurses": 12,
        "support_workers": 6,
        "medical_staff": 3,
        "agency_hours": 10,
        "vacancy_rate": 0.08,
        "admission_datetime": "2026-01-15T10:30:00",
    }
