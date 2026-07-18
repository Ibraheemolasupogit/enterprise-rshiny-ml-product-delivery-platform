"""Local lifecycle provider backed by the existing registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ml_product.lifecycle.config import LocalLifecycleConfig
from ml_product.lifecycle.identity import registration_fingerprint
from ml_product.lifecycle.models import (
    ApprovalEvidenceReference,
    ChallengerReference,
    ChampionChallengerComparison,
    ChampionReference,
    LifecycleStatusTransition,
    PromotionDecision,
    PromotionRequest,
    PromotionResult,
    RegistrationResult,
)
from ml_product.lifecycle.package import ModelLifecyclePackage
from ml_product.lifecycle.promotion import (
    build_champion_challenger_comparison,
    promotion_decision,
    reconcile_external_lifecycle,
)
from ml_product.registry.config import GovernanceConfig, RegistryConfig
from ml_product.registry.registry import LocalModelRegistry


class LocalLifecycleProvider:
    provider_name = "local"

    def __init__(self, config: LocalLifecycleConfig, *, root: Path = Path(".")) -> None:
        self.registry = LocalModelRegistry(
            RegistryConfig.from_file(config.registry_config),
            GovernanceConfig.from_file(config.governance_config),
            root=root,
        )

    def readiness_check(self) -> dict[str, Any]:
        validation = self.registry.validate()
        return {
            "provider": self.provider_name,
            "provider_label": "local_model_lifecycle",
            "healthy": bool(validation.get("valid")),
            "errors": validation.get("errors", []),
        }

    def register_model_package(
        self,
        package: ModelLifecyclePackage,
        *,
        dry_run: bool = False,
    ) -> RegistrationResult:
        del dry_run
        version = self.registry.get_model_version(package.model_name, package.model_version)
        fingerprint = registration_fingerprint(package)
        return RegistrationResult(
            provider=self.provider_name,
            registration_status="already_registered",
            local_model_id=version.registry_id,
            local_model_version=version.registry_version,
            local_build_identifier=version.candidate_identifier,
            external_project_id="local-filesystem-registry",
            external_model_id=version.registry_id,
            external_model_version_id=f"v{version.registry_version:06d}",
            registration_fingerprint=fingerprint,
            registered_timestamp_utc=version.created_at_utc,
            metadata_synchronisation_status="synchronised",
            warnings=["Local provider delegates to the existing registry; no external call made."],
        )

    def retrieve_model_metadata(self, model_name: str, version: int) -> dict[str, Any]:
        model_version = self.registry.get_model_version(model_name, version)
        return model_version.model_dump(mode="json")

    def submit_lifecycle_status(
        self, model_name: str, version: int, status: str, *, actor: str, reason: str
    ) -> dict[str, Any]:
        if status == "approval_pending":
            return self.registry.submit_for_approval(model_name, version).model_dump(mode="json")
        if status in {"approve", "approve_with_conditions", "reject", "defer"}:
            return self.registry.record_approval_decision(
                model_name=model_name,
                version=version,
                decision=status,  # type: ignore[arg-type]
                actor=actor,
                reason=reason,
                conditions=[],
            ).model_dump(mode="json")
        raise ValueError(f"Unsupported local lifecycle status: {status}")

    def promote_model_version(
        self, model_name: str, version: int, *, actor: str, reason: str
    ) -> dict[str, Any]:
        return self.registry.activate_model(
            model_name=model_name,
            version=version,
            actor=actor,
            reason=reason,
        ).model_dump(mode="json")

    def retrieve_current_champion(self, model_name: str) -> ChampionReference | None:
        active = self.registry.get_active_model()
        if active is None or active.model_name != model_name:
            return None
        return ChampionReference(
            provider=self.provider_name,
            model_name=active.model_name,
            local_model_id=active.registry_id,
            local_model_version=active.registry_version,
            external_model_id=active.registry_id,
            external_model_version_id=f"v{active.registry_version:06d}",
            registration_fingerprint=None,
            lifecycle_state=active.status,
        )

    def retrieve_registered_challengers(
        self, package: ModelLifecyclePackage
    ) -> list[ChallengerReference]:
        del package
        challengers: list[ChallengerReference] = []
        for version in self.registry.list_models():
            challengers.append(
                ChallengerReference(
                    provider=self.provider_name,
                    model_name=version.model_name,
                    local_model_id=version.registry_id,
                    local_model_version=version.registry_version,
                    local_build_identifier=version.candidate_identifier,
                    external_model_id=version.registry_id,
                    external_model_version_id=f"v{version.registry_version:06d}",
                    registration_fingerprint=version.evidence_fingerprint,
                    lifecycle_state=version.status,
                )
            )
        return challengers

    def compare_champion_and_challenger(
        self, package: ModelLifecyclePackage
    ) -> ChampionChallengerComparison:
        return build_champion_challenger_comparison(
            package,
            provider=self.provider_name,
            champion=self.retrieve_current_champion(package.model_name),
            linkage=None,
        )

    def submit_promotion_request(
        self, package: ModelLifecyclePackage, *, dry_run: bool = False
    ) -> PromotionResult:
        del dry_run
        comparison = self.compare_champion_and_challenger(package)
        decision = promotion_decision(comparison)
        champion = self.retrieve_current_champion(package.model_name)
        return PromotionResult(
            provider=self.provider_name,
            promotion_status=decision.status,
            local_model_id=package.registry_id,
            local_model_version=package.model_version,
            external_model_id=package.registry_id,
            external_model_version_id=f"v{package.model_version:06d}",
            registration_fingerprint=registration_fingerprint(package),
            champion_before=champion,
            champion_after=champion,
            approval=decision.approval,
            blocking_reasons=decision.blocking_reasons,
            local_activation_performed=False,
            reconciliation=reconcile_external_lifecycle(
                local_active_version=None
                if champion is None
                else champion.local_model_version,
                external_champion=champion,
            ),
        )

    def record_approval_status(
        self, package: ModelLifecyclePackage, *, status: str, actor: str, reason: str
    ) -> LifecycleStatusTransition:
        return LifecycleStatusTransition(
            provider=self.provider_name,
            model_name=package.model_name,
            model_version=package.model_version,
            previous_state=str(package.governance_status.get("registry_status")),
            target_state=status,
            accepted=False,
            reason=(
                f"Local approval changes must use existing registry commands. "
                f"Requested by {actor}: {reason}"
            ),
        )

    def promote_approved_model_version(
        self, request: PromotionRequest, *, confirm_external: bool = False
    ) -> PromotionResult:
        del confirm_external
        champion = self.retrieve_current_champion(request.model_name)
        return PromotionResult(
            provider=self.provider_name,
            promotion_status="blocked",
            local_model_id=request.local_model_id,
            local_model_version=request.local_model_version,
            external_model_id=request.external_model_id,
            external_model_version_id=request.external_model_version_id,
            registration_fingerprint=request.registration_fingerprint,
            champion_before=champion,
            champion_after=champion,
            approval=ApprovalEvidenceReference(approval_status="missing"),
            blocking_reasons=[
                "Local activation remains a separate explicit governed registry command."
            ],
            local_activation_performed=False,
            reconciliation=reconcile_external_lifecycle(
                local_active_version=None if champion is None else champion.local_model_version,
                external_champion=champion,
            ),
        )

    def retrieve_promotion_state(self, package: ModelLifecyclePackage) -> PromotionDecision:
        return promotion_decision(self.compare_champion_and_challenger(package))

    def reconcile_lifecycle_state(self, package: ModelLifecyclePackage) -> PromotionResult:
        return self.submit_promotion_request(package, dry_run=True)
