"""SAS Viya lifecycle provider boundary."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ml_product.lifecycle.config import RegistrationConfig, SasViyaConfig
from ml_product.lifecycle.identity import registration_fingerprint
from ml_product.lifecycle.linkage import LinkageStore, sha256_json
from ml_product.lifecycle.metadata import build_sas_viya_metadata, reconcile_metadata
from ml_product.lifecycle.models import (
    LinkageRecord,
    MetadataSyncStatus,
    RegistrationResult,
    RegistrationStatus,
)
from ml_product.lifecycle.package import ModelLifecyclePackage
from ml_product.lifecycle.sas_viya_client import HttpTransport, SasViyaClient
from ml_product.utils.paths import repository_root


class SasViyaLifecycleProvider:
    """Provider facade for future live SAS Viya lifecycle operations."""

    provider_name = "sas_viya"

    def __init__(
        self,
        config: SasViyaConfig,
        *,
        registration_config: RegistrationConfig | None = None,
        transport: HttpTransport | None = None,
    ) -> None:
        self.config = config
        self.registration_config = registration_config or RegistrationConfig()
        self.client = SasViyaClient(config, transport=transport)

    def readiness_check(self) -> dict[str, Any]:
        return self.client.readiness_check()

    def register_model_package(
        self,
        package: ModelLifecyclePackage,
        *,
        dry_run: bool = False,
    ) -> RegistrationResult:
        fingerprint = registration_fingerprint(package)
        metadata = build_sas_viya_metadata(package)
        timestamp = _timestamp()
        if dry_run:
            return RegistrationResult(
                provider=self.provider_name,
                registration_status="reconciled",
                local_model_id=package.registry_id,
                local_model_version=package.model_version,
                local_build_identifier=package.candidate_identifier,
                external_project_id=self.config.model_repository_identifier,
                external_model_id=None,
                external_model_version_id=None,
                registration_fingerprint=fingerprint,
                registered_timestamp_utc=timestamp,
                metadata_synchronisation_status="not_attempted",
                warnings=["Dry run only; no SAS Viya API calls were made."],
            )

        repository = self.client.resolve_target_repository()
        repository_id = _required_id(repository, "repository")
        model = self.client.find_model_by_identity(repository_id, package.model_name)
        model_created = model is None
        if model is None:
            model = self.client.create_model(repository_id, metadata["model"])
        model_id = _required_id(model, "model")
        version = self.client.find_model_version_by_fingerprint(model_id, fingerprint)
        version_created = version is None
        if version is None:
            version = self.client.create_model_version(model_id, metadata["version"])
        version_id = _required_id(version, "model version")
        synced_metadata = self.client.synchronise_metadata(
            model_id,
            version_id,
            metadata["metadata"],
        )
        external_version = self.client.retrieve_model_version_metadata(model_id, version_id)
        reconciliation = reconcile_metadata(package, synced_metadata or external_version)
        sync_status: MetadataSyncStatus = (
            "synchronised"
            if reconciliation.status in {"matched", "missing_external"}
            else "mismatch"
        )
        status: RegistrationStatus = (
            "registered" if model_created or version_created else "already_registered"
        )
        result = RegistrationResult(
            provider=self.provider_name,
            registration_status=status,
            local_model_id=package.registry_id,
            local_model_version=package.model_version,
            local_build_identifier=package.candidate_identifier,
            external_project_id=repository_id,
            external_model_id=model_id,
            external_model_version_id=version_id,
            registration_fingerprint=fingerprint,
            registered_timestamp_utc=timestamp,
            metadata_synchronisation_status=sync_status,
            warnings=[],
            reconciliation=reconciliation,
        )
        evidence_path, evidence_checksum = self._write_evidence(
            package,
            result,
            metadata,
            model_created=model_created,
            version_created=version_created,
        )
        result = result.model_copy(update={"evidence_path": evidence_path})
        self._upsert_linkage(result, evidence_checksum)
        return result

    def retrieve_model_metadata(self, model_name: str, version: int) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model_name": model_name,
            "model_version": version,
            "status": "not_queried",
            "reason": "Milestone 15.1 does not call live SAS Viya model metadata APIs.",
        }

    def submit_lifecycle_status(
        self, model_name: str, version: int, status: str, *, actor: str, reason: str
    ) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "accepted": False,
            "model_name": model_name,
            "model_version": version,
            "requested_status": status,
            "actor": actor,
            "reason": reason,
            "boundary": "No live SAS Viya lifecycle mutation is implemented in Milestone 15.1.",
        }

    def promote_model_version(
        self, model_name: str, version: int, *, actor: str, reason: str
    ) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "accepted": False,
            "model_name": model_name,
            "model_version": version,
            "actor": actor,
            "reason": reason,
            "boundary": "No live SAS Viya promotion is implemented in Milestone 15.1.",
        }

    def retrieve_current_champion(self, model_name: str) -> dict[str, Any] | None:
        return {
            "provider": self.provider_name,
            "model_name": model_name,
            "status": "not_queried",
            "reason": "Milestone 15.1 does not call live SAS Viya champion APIs.",
        }

    def _write_evidence(
        self,
        package: ModelLifecyclePackage,
        result: RegistrationResult,
        metadata: dict[str, Any],
        *,
        model_created: bool,
        version_created: bool,
    ) -> tuple[str, str]:
        evidence_dir = _resolve(self.registration_config.evidence_directory)
        evidence_dir.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "schema_version": "lifecycle-registration-evidence/v1",
            "provider": self.provider_name,
            "package_fingerprint": result.registration_fingerprint,
            "registration_request_summary": {
                "model_name": package.model_name,
                "model_version": package.model_version,
                "model_family": package.model_family,
                "target_repository": self.config.model_repository_identifier,
            },
            "response_identifiers": {
                "external_project_id": result.external_project_id,
                "external_model_id": result.external_model_id,
                "external_model_version_id": result.external_model_version_id,
            },
            "idempotency_decision": {
                "model_created": model_created,
                "version_created": version_created,
                "registration_status": result.registration_status,
            },
            "metadata_mapping_summary": {
                "custom_property_count": len(
                    metadata.get("metadata", {}).get("customProperties", {})
                ),
                "contains_metrics": "metrics" in metadata.get("metadata", {}),
                "contains_governance": "governance" in metadata.get("metadata", {}),
            },
            "reconciliation_result": None
            if result.reconciliation is None
            else result.reconciliation.model_dump(mode="json"),
            "registered_timestamp_utc": result.registered_timestamp_utc,
        }
        checksum = sha256_json(payload)
        payload["evidence_checksum"] = checksum
        path = evidence_dir / f"{result.registration_fingerprint}.json"
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        try:
            display_path = path.relative_to(repository_root())
        except ValueError:
            display_path = path
        return str(display_path), checksum

    def _upsert_linkage(self, result: RegistrationResult, evidence_checksum: str) -> None:
        store = LinkageStore(self.registration_config.linkage_path)
        existing = store.find(self.provider_name, result.registration_fingerprint)
        first_registered_at = (
            existing.first_registered_at_utc
            if existing is not None
            else result.registered_timestamp_utc
        )
        store.upsert(
            LinkageRecord(
                provider=self.provider_name,
                local_model_id=result.local_model_id,
                local_model_version=result.local_model_version,
                local_build_identifier=result.local_build_identifier,
                registration_fingerprint=result.registration_fingerprint,
                external_project_id=result.external_project_id,
                external_model_id=result.external_model_id,
                external_model_version_id=result.external_model_version_id,
                metadata_sync_status=result.metadata_synchronisation_status,
                first_registered_at_utc=first_registered_at,
                last_reconciled_at_utc=result.registered_timestamp_utc,
                evidence_path=result.evidence_path,
                evidence_checksum=evidence_checksum,
            )
        )


def _timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _required_id(payload: dict[str, Any], resource: str) -> str:
    value = payload.get("id")
    if not isinstance(value, str) or not value:
        raise ValueError(f"SAS Viya {resource} response did not include an id.")
    return value


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else repository_root() / path
