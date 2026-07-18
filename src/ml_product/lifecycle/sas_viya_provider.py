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
    ApprovalEvidenceReference,
    ChallengerReference,
    ChampionChallengerComparison,
    ChampionReference,
    LifecycleStatusTransition,
    LinkageRecord,
    MetadataSyncStatus,
    PromotionDecision,
    PromotionRequest,
    PromotionResult,
    RegistrationResult,
    RegistrationStatus,
)
from ml_product.lifecycle.package import ModelLifecyclePackage
from ml_product.lifecycle.promotion import (
    approval_reference,
    build_champion_challenger_comparison,
    challenger_from_package,
    linkage_for_package,
    promotion_decision,
    reconcile_external_lifecycle,
    write_promotion_evidence,
)
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
            "boundary": "Use lifecycle-submit-promotion for external-only promotion.",
        }

    def retrieve_current_champion(self, model_name: str) -> ChampionReference | None:
        del model_name
        repository = self.client.resolve_target_repository()
        champion = self.client.get_current_champion(_required_id(repository, "repository"))
        if champion is None:
            return None
        return _champion_from_payload(self.provider_name, champion)

    def retrieve_registered_challengers(
        self, package: ModelLifecyclePackage
    ) -> list[ChallengerReference]:
        repository = self.client.resolve_target_repository()
        payloads = self.client.list_challengers(_required_id(repository, "repository"))
        if payloads:
            return [_challenger_from_payload(self.provider_name, item) for item in payloads]
        linkage = linkage_for_package(
            package,
            provider=self.provider_name,
            linkage_path=self.registration_config.linkage_path,
        )
        return [challenger_from_package(package, provider=self.provider_name, linkage=linkage)]

    def compare_champion_and_challenger(
        self, package: ModelLifecyclePackage
    ) -> ChampionChallengerComparison:
        linkage = linkage_for_package(
            package,
            provider=self.provider_name,
            linkage_path=self.registration_config.linkage_path,
        )
        return build_champion_challenger_comparison(
            package,
            provider=self.provider_name,
            champion=self.retrieve_current_champion(package.model_name),
            linkage=linkage,
        )

    def submit_promotion_request(
        self, package: ModelLifecyclePackage, *, dry_run: bool = False
    ) -> PromotionResult:
        comparison = self.compare_champion_and_challenger(package)
        decision = promotion_decision(comparison)
        champion = comparison.champion
        if dry_run or decision.status != "eligible":
            return PromotionResult(
                provider=self.provider_name,
                promotion_status=decision.status,
                local_model_id=package.registry_id,
                local_model_version=package.model_version,
                external_model_id=comparison.challenger.external_model_id,
                external_model_version_id=comparison.challenger.external_model_version_id,
                registration_fingerprint=comparison.challenger.registration_fingerprint,
                champion_before=champion,
                champion_after=champion,
                approval=decision.approval,
                blocking_reasons=decision.blocking_reasons,
                local_activation_performed=False,
                reconciliation=reconcile_external_lifecycle(
                    local_active_version=None,
                    external_champion=champion,
                ),
            )
        request = PromotionRequest(
            provider=self.provider_name,
            model_name=package.model_name,
            local_model_id=package.registry_id,
            local_model_version=package.model_version,
            external_model_id=comparison.challenger.external_model_id,
            external_model_version_id=comparison.challenger.external_model_version_id,
            registration_fingerprint=comparison.challenger.registration_fingerprint,
            requested_by="SAS-VIYA-LIFECYCLE",
            reason="External lifecycle promotion after approval.",
        )
        return self.promote_approved_model_version(request, confirm_external=True)

    def record_approval_status(
        self, package: ModelLifecyclePackage, *, status: str, actor: str, reason: str
    ) -> LifecycleStatusTransition:
        linkage = linkage_for_package(
            package,
            provider=self.provider_name,
            linkage_path=self.registration_config.linkage_path,
        )
        if (
            linkage is None
            or linkage.external_model_id is None
            or linkage.external_model_version_id is None
        ):
            return LifecycleStatusTransition(
                provider=self.provider_name,
                model_name=package.model_name,
                model_version=package.model_version,
                previous_state=None,
                target_state=status,
                accepted=False,
                reason="Cannot synchronise approval before external registration linkage exists.",
            )
        self.client.update_approval_metadata(
            linkage.external_model_id,
            linkage.external_model_version_id,
            {"status": status, "actor": actor, "reason": reason},
        )
        return LifecycleStatusTransition(
            provider=self.provider_name,
            model_name=package.model_name,
            model_version=package.model_version,
            previous_state=str(package.governance_status.get("registry_status")),
            target_state=status,
            accepted=True,
            reason=reason,
        )

    def promote_approved_model_version(
        self, request: PromotionRequest, *, confirm_external: bool = False
    ) -> PromotionResult:
        champion_before = self.retrieve_current_champion(request.model_name)
        if champion_before is not None and (
            champion_before.registration_fingerprint == request.registration_fingerprint
            or champion_before.external_model_version_id == request.external_model_version_id
        ):
            return PromotionResult(
                provider=self.provider_name,
                promotion_status="already_champion",
                local_model_id=request.local_model_id,
                local_model_version=request.local_model_version,
                external_model_id=request.external_model_id,
                external_model_version_id=request.external_model_version_id,
                registration_fingerprint=request.registration_fingerprint,
                champion_before=champion_before,
                champion_after=champion_before,
                approval=ApprovalEvidenceReference(approval_status="approved"),
                local_activation_performed=False,
                reconciliation=reconcile_external_lifecycle(
                    local_active_version=None,
                    external_champion=champion_before,
                ),
            )
        if not confirm_external:
            return PromotionResult(
                provider=self.provider_name,
                promotion_status="blocked",
                local_model_id=request.local_model_id,
                local_model_version=request.local_model_version,
                external_model_id=request.external_model_id,
                external_model_version_id=request.external_model_version_id,
                registration_fingerprint=request.registration_fingerprint,
                champion_before=champion_before,
                champion_after=champion_before,
                approval=ApprovalEvidenceReference(approval_status="approved"),
                blocking_reasons=["External promotion requires --confirm-external-promotion."],
                local_activation_performed=False,
            )
        if request.external_model_id is None or request.external_model_version_id is None:
            raise ValueError("External model and version ids are required for promotion.")
        self.client.promote_model_version(
            request.external_model_id,
            request.external_model_version_id,
        )
        repository = self.client.resolve_target_repository()
        self.client.assign_champion(
            _required_id(repository, "repository"),
            request.external_model_id,
            request.external_model_version_id,
        )
        champion_after = self.retrieve_current_champion(request.model_name)
        result = PromotionResult(
            provider=self.provider_name,
            promotion_status="promoted",
            local_model_id=request.local_model_id,
            local_model_version=request.local_model_version,
            external_model_id=request.external_model_id,
            external_model_version_id=request.external_model_version_id,
            registration_fingerprint=request.registration_fingerprint,
            champion_before=champion_before,
            champion_after=champion_after,
            approval=ApprovalEvidenceReference(approval_status="approved"),
            local_activation_performed=False,
            reconciliation=reconcile_external_lifecycle(
                local_active_version=None,
                external_champion=champion_after,
            ),
        )
        return write_promotion_evidence(
            result,
            evidence_directory=self.registration_config.promotion_evidence_directory,
        )

    def retrieve_promotion_state(self, package: ModelLifecyclePackage) -> PromotionDecision:
        try:
            return promotion_decision(self.compare_champion_and_challenger(package))
        except Exception:
            comparison = build_champion_challenger_comparison(
                package,
                provider=self.provider_name,
                champion=None,
                linkage=linkage_for_package(
                    package,
                    provider=self.provider_name,
                    linkage_path=self.registration_config.linkage_path,
                ),
            )
            return promotion_decision(comparison)

    def reconcile_lifecycle_state(self, package: ModelLifecyclePackage) -> PromotionResult:
        comparison = self.compare_champion_and_challenger(package)
        decision = promotion_decision(comparison)
        return PromotionResult(
            provider=self.provider_name,
            promotion_status=decision.status,
            local_model_id=package.registry_id,
            local_model_version=package.model_version,
            external_model_id=comparison.challenger.external_model_id,
            external_model_version_id=comparison.challenger.external_model_version_id,
            registration_fingerprint=comparison.challenger.registration_fingerprint,
            champion_before=comparison.champion,
            champion_after=comparison.champion,
            approval=approval_reference(package),
            blocking_reasons=decision.blocking_reasons,
            local_activation_performed=False,
            reconciliation=reconcile_external_lifecycle(
                local_active_version=None,
                external_champion=comparison.champion,
            ),
        )

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


def _champion_from_payload(provider: str, payload: dict[str, Any]) -> ChampionReference:
    return ChampionReference(
        provider=provider,
        model_name=str(payload.get("modelName") or payload.get("name") or "unknown"),
        local_model_id=_optional_str(payload.get("localModelId")),
        local_model_version=_optional_int(payload.get("localModelVersion")),
        external_model_id=_optional_str(payload.get("modelId") or payload.get("id")),
        external_model_version_id=_optional_str(payload.get("versionId")),
        registration_fingerprint=_optional_str(payload.get("registrationFingerprint")),
        lifecycle_state=str(payload.get("lifecycleState") or payload.get("state") or "champion"),
    )


def _challenger_from_payload(provider: str, payload: dict[str, Any]) -> ChallengerReference:
    return ChallengerReference(
        provider=provider,
        model_name=str(payload.get("modelName") or payload.get("name") or "unknown"),
        local_model_id=str(payload.get("localModelId") or "unknown"),
        local_model_version=int(payload.get("localModelVersion") or 0),
        local_build_identifier=str(payload.get("localBuildIdentifier") or "unknown"),
        external_model_id=_optional_str(payload.get("modelId") or payload.get("id")),
        external_model_version_id=_optional_str(payload.get("versionId")),
        registration_fingerprint=str(payload.get("registrationFingerprint") or ""),
        lifecycle_state=str(payload.get("lifecycleState") or payload.get("state") or "registered"),
    )


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) else None
