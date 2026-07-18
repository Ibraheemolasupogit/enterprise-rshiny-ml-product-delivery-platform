"""Provider-neutral lifecycle protocol."""

from __future__ import annotations

from typing import Any, Protocol

from ml_product.lifecycle.models import (
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


class ModelLifecycleProvider(Protocol):
    provider_name: str

    def readiness_check(self) -> dict[str, Any]: ...

    def register_model_package(
        self,
        package: ModelLifecyclePackage,
        *,
        dry_run: bool = False,
    ) -> RegistrationResult: ...

    def retrieve_model_metadata(self, model_name: str, version: int) -> dict[str, Any]: ...

    def submit_lifecycle_status(
        self, model_name: str, version: int, status: str, *, actor: str, reason: str
    ) -> dict[str, Any]: ...

    def promote_model_version(
        self, model_name: str, version: int, *, actor: str, reason: str
    ) -> dict[str, Any]: ...

    def retrieve_current_champion(self, model_name: str) -> ChampionReference | None: ...

    def retrieve_registered_challengers(
        self, package: ModelLifecyclePackage
    ) -> list[ChallengerReference]: ...

    def compare_champion_and_challenger(
        self, package: ModelLifecyclePackage
    ) -> ChampionChallengerComparison: ...

    def submit_promotion_request(
        self, package: ModelLifecyclePackage, *, dry_run: bool = False
    ) -> PromotionResult: ...

    def record_approval_status(
        self, package: ModelLifecyclePackage, *, status: str, actor: str, reason: str
    ) -> LifecycleStatusTransition: ...

    def promote_approved_model_version(
        self, request: PromotionRequest, *, confirm_external: bool = False
    ) -> PromotionResult: ...

    def retrieve_promotion_state(self, package: ModelLifecyclePackage) -> PromotionDecision: ...

    def reconcile_lifecycle_state(self, package: ModelLifecyclePackage) -> PromotionResult: ...
