"""Future Denodo adapter boundary.

This module is intentionally not implemented in Milestone 3. It exists only to
document the interface boundary and prevent the local DuckDB layer from being
misrepresented as real Denodo.
"""

from __future__ import annotations

from typing import Any


class DenodoClient:
    provider = "real_denodo"
    implemented = False

    def provider_info(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "implemented": self.implemented,
            "status": "not implemented",
        }

    def health_check(self) -> dict[str, Any]:
        return {"healthy": False, "status": "real Denodo integration is not implemented"}

    def __getattr__(self, name: str) -> Any:
        raise NotImplementedError("Real Denodo integration is not implemented in Milestone 3")
