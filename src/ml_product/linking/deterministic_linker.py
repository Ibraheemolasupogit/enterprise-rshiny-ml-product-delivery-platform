"""Deterministic source linking rules for Milestone 3."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def admission_context_key(admission: dict[str, Any]) -> tuple[str, str]:
    admission_date = datetime.fromisoformat(str(admission["admission_datetime"])).date().isoformat()
    return str(admission["ward_id"]), admission_date


def unresolved_foreign_keys(
    child_rows: list[dict[str, Any]],
    *,
    child_key: str,
    parent_keys: set[str],
) -> list[str]:
    return sorted(
        str(row[child_key]) for row in child_rows if str(row[child_key]) not in parent_keys
    )
