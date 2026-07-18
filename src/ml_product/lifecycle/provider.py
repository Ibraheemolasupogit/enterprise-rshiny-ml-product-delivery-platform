"""Provider-neutral lifecycle protocol."""

from __future__ import annotations

from typing import Any, Protocol


class ModelLifecycleProvider(Protocol):
    provider_name: str

    def readiness_check(self) -> dict[str, Any]: ...

    def register_model_package(self, package: dict[str, Any]) -> dict[str, Any]: ...

    def retrieve_model_metadata(self, model_name: str, version: int) -> dict[str, Any]: ...

    def submit_lifecycle_status(
        self, model_name: str, version: int, status: str, *, actor: str, reason: str
    ) -> dict[str, Any]: ...

    def promote_model_version(
        self, model_name: str, version: int, *, actor: str, reason: str
    ) -> dict[str, Any]: ...

    def retrieve_current_champion(self, model_name: str) -> dict[str, Any] | None: ...
