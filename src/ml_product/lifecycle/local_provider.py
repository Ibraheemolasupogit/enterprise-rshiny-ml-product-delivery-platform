"""Local lifecycle provider backed by the existing registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ml_product.lifecycle.config import LocalLifecycleConfig
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

    def register_model_package(self, package: dict[str, Any]) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "accepted": False,
            "reason": (
                "Milestone 15.1 builds review packages only; "
                "local registration is unchanged."
            ),
            "model_name": package.get("model_name"),
            "model_version": package.get("model_version"),
        }

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

    def retrieve_current_champion(self, model_name: str) -> dict[str, Any] | None:
        active = self.registry.get_active_model()
        if active is None or active.model_name != model_name:
            return None
        return active.model_dump(mode="json")
