"""SAS Viya lifecycle provider boundary."""

from __future__ import annotations

from typing import Any

from ml_product.lifecycle.config import SasViyaConfig
from ml_product.lifecycle.sas_viya_client import HttpTransport, SasViyaClient


class SasViyaLifecycleProvider:
    """Provider facade for future live SAS Viya lifecycle operations."""

    provider_name = "sas_viya"

    def __init__(
        self,
        config: SasViyaConfig,
        *,
        transport: HttpTransport | None = None,
    ) -> None:
        self.config = config
        self.client = SasViyaClient(config, transport=transport)

    def readiness_check(self) -> dict[str, Any]:
        return self.client.readiness_check()

    def register_model_package(self, package: dict[str, Any]) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "accepted": False,
            "reason": (
                "Milestone 15.1 defines the SAS Viya client boundary; "
                "live registration is not enabled."
            ),
            "model_name": package.get("model_name"),
            "model_version": package.get("model_version"),
            "target_repository": self.config.model_repository_identifier,
        }

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
