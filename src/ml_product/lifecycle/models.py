"""Typed lifecycle registration domain models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RegistrationStatus = Literal["registered", "already_registered", "reconciled", "failed"]
MetadataSyncStatus = Literal["not_attempted", "synchronised", "mismatch", "failed"]
ReconciliationStatus = Literal["matched", "mismatch", "missing_external", "unsupported"]


class ReconciliationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ReconciliationStatus
    matched_fields: dict[str, Any] = Field(default_factory=dict)
    mismatches: dict[str, dict[str, Any]] = Field(default_factory=dict)
    missing_external_fields: list[str] = Field(default_factory=list)
    unsupported_fields: list[str] = Field(default_factory=list)


class RegistrationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    registration_status: RegistrationStatus
    local_model_id: str
    local_model_version: int
    local_build_identifier: str
    external_project_id: str | None
    external_model_id: str | None
    external_model_version_id: str | None
    registration_fingerprint: str
    registered_timestamp_utc: str
    metadata_synchronisation_status: MetadataSyncStatus
    warnings: list[str] = Field(default_factory=list)
    evidence_path: str | None = None
    reconciliation: ReconciliationResult | None = None


class LinkageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    local_model_id: str
    local_model_version: int
    local_build_identifier: str
    registration_fingerprint: str
    external_project_id: str | None
    external_model_id: str | None
    external_model_version_id: str | None
    metadata_sync_status: MetadataSyncStatus
    first_registered_at_utc: str
    last_reconciled_at_utc: str
    evidence_path: str | None = None
    evidence_checksum: str | None = None


class LinkageStorePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "lifecycle-linkage/v1"
    records: list[LinkageRecord] = Field(default_factory=list)
