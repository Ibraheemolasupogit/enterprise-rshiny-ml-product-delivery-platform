from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from ml_product.serving.app import create_app
from ml_product.serving.config import ServingConfig

ACCEPTED_FIELDS = {
    "age",
    "sex",
    "postcode_region",
    "deprivation_decile",
    "comorbidity_count",
    "previous_admissions_12m",
    "admission_type",
    "source_of_admission",
    "initial_news2_score",
    "mobility_status",
    "primary_diagnosis_group",
    "primary_diagnosis_complexity",
    "diagnosis_count",
    "secondary_diagnosis_count",
    "staffed_beds",
    "occupied_beds",
    "closed_beds",
    "isolation_capacity",
    "registered_nurses",
    "support_workers",
    "medical_staff",
    "agency_hours",
    "vacancy_rate",
    "occupancy_rate",
    "staff_to_bed_ratio",
    "admission_datetime",
    "request_id",
}

PROHIBITED_FIELDS = {
    "patient_id",
    "admission_id",
    "discharge_datetime",
    "length_of_stay_days",
    "long_stay_flag",
    "readmission_30d",
    "discharge_destination",
}


def test_openapi_request_schema_matches_r_client_contract() -> None:
    schema = create_app().openapi()["components"]["schemas"]["PredictionRequest"]
    properties = set(schema["properties"])
    assert properties == ACCEPTED_FIELDS
    assert PROHIBITED_FIELDS.isdisjoint(properties)
    assert schema["additionalProperties"] is False


def test_response_schema_matches_r_parser_expectations() -> None:
    schema = create_app().openapi()["components"]["schemas"]["PredictionResponse"]
    assert set(schema["properties"]) == {
        "prediction",
        "model",
        "explanation",
        "limitations",
        "request",
    }


def test_local_cors_origins_are_bounded() -> None:
    config = ServingConfig.from_file(Path("config/serving.yaml"))
    assert config.cors.enabled is True
    assert config.cors.allow_credentials is False
    assert "*" not in config.cors.allowed_origins
    assert config.cors.allowed_origins == [
        "http://127.0.0.1:3838",
        "http://localhost:3838",
    ]


def test_not_ready_error_format_is_stable(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_API_KEY", "test-key")
    client = TestClient(create_app())
    response = client.post(
        "/v1/predict",
        headers={"X-API-Key": "test-key"},
        json={"age": 80},
    )
    assert response.status_code in {422, 503}
    assert "detail" in response.json()
