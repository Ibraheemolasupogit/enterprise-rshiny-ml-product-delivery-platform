"""Model comparison table helpers."""

from __future__ import annotations

from typing import Any


def comparison_payload(rows: list[dict[str, Any]], selection_rule: str) -> dict[str, Any]:
    return {
        "selection_dataset": "validation",
        "test_set_used_for_selection": False,
        "selection_rule": selection_rule,
        "rows": rows,
    }
