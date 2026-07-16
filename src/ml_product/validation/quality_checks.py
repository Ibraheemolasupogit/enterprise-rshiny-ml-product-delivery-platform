"""Quality reconciliation checks."""

from __future__ import annotations

from collections import Counter
from typing import Any


def issue_counts(issues: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(issue["issue_type"]) for issue in issues))
