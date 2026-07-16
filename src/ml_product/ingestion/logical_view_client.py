"""Provider-neutral logical-view client interface."""

from __future__ import annotations

from typing import Any, Protocol


class LogicalViewClient(Protocol):
    def list_views(self) -> list[str]: ...
    def describe_view(self, view_name: str) -> dict[str, Any]: ...
    def query_view(
        self,
        view_name: str,
        columns: list[str] | None = None,
        filters: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]: ...
    def get_lineage(self, view_name: str) -> list[str]: ...
    def health_check(self) -> dict[str, Any]: ...
    def provider_info(self) -> dict[str, Any]: ...
