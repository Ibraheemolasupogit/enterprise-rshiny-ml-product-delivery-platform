"""Duplicate-key detection for source-system records."""

from __future__ import annotations

from collections import Counter
from typing import Any


def duplicate_keys(rows: list[dict[str, Any]], key: str) -> list[str]:
    counts = Counter(str(row[key]) for row in rows)
    return sorted(identifier for identifier, count in counts.items() if count > 1)
