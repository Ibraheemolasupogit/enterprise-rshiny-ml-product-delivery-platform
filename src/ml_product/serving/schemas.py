"""API request and response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Sex = Literal["female", "male", "not_specified"]
PostcodeRegion = Literal["SR-CENTRAL", "SR-EAST", "SR-NORTH", "SR-SOUTH", "SR-WEST"]
AdmissionType = Literal["emergency", "planned", "urgent"]
SourceOfAdmission = Literal["care_facility", "clinic", "home", "transfer"]
MobilityStatus = Literal["assisted", "bedbound", "independent", "limited"]
DiagnosisGroup = Literal[
    "cardiovascular_synthetic",
    "frailty_synthetic",
    "infection_synthetic",
    "other_synthetic",
    "respiratory_synthetic",
    "surgical_synthetic",
]
DiagnosisComplexity = Literal["high", "low", "moderate"]


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: float = Field(ge=18, le=110)
    sex: Sex
    postcode_region: PostcodeRegion
    deprivation_decile: int = Field(ge=1, le=10)
    comorbidity_count: float = Field(ge=0)
    previous_admissions_12m: float = Field(ge=0)
    admission_type: AdmissionType
    source_of_admission: SourceOfAdmission
    initial_news2_score: float = Field(ge=0, le=20)
    mobility_status: MobilityStatus
    primary_diagnosis_group: DiagnosisGroup
    primary_diagnosis_complexity: DiagnosisComplexity
    diagnosis_count: float = Field(ge=1)
    secondary_diagnosis_count: float = Field(ge=0)
    staffed_beds: float = Field(gt=0)
    occupied_beds: float = Field(ge=0)
    closed_beds: float = Field(ge=0)
    isolation_capacity: float = Field(ge=0)
    registered_nurses: float = Field(ge=0)
    support_workers: float = Field(ge=0)
    medical_staff: float = Field(ge=0)
    agency_hours: float = Field(ge=0)
    vacancy_rate: float = Field(ge=0, le=1)
    occupancy_rate: float | None = Field(default=None, ge=0, le=1.5)
    staff_to_bed_ratio: float | None = Field(default=None, ge=0)
    admission_datetime: datetime
    request_id: str | None = Field(default=None, max_length=80)

    @model_validator(mode="before")
    @classmethod
    def reject_outcome_or_identifier_fields(cls, data: object) -> object:
        if isinstance(data, dict):
            prohibited = {
                "discharge_datetime",
                "length_of_stay_days",
                "long_stay_flag",
                "readmission_30d",
                "discharge_destination",
                "patient_id",
                "admission_id",
            }
            present = prohibited.intersection(data)
            if present:
                raise ValueError(
                    f"Outcome or identifier fields are not accepted: {sorted(present)}"
                )
        return data

    @field_validator("occupied_beds")
    @classmethod
    def beds_are_non_negative(cls, value: float) -> float:
        return value


class BatchPredictionRequest(BaseModel):
    records: list[PredictionRequest]


class PredictionPayload(BaseModel):
    long_stay_probability: float
    predicted_long_stay: bool
    risk_band: Literal["low", "medium", "high"]


class ModelPayload(BaseModel):
    model_name: str
    registry_version: int
    candidate_identifier: str
    model_family: str
    calibration: str
    threshold: float
    approval_status: str
    activation_status: str


class ExplanationPayload(BaseModel):
    method: str
    important_factors: list[str]
    warning: str


class RequestPayload(BaseModel):
    request_id: str
    review_mode: bool
    status: list[str]


class PredictionResponse(BaseModel):
    prediction: PredictionPayload
    model: ModelPayload
    explanation: ExplanationPayload
    limitations: list[str]
    request: RequestPayload
