"""Linkage-quality metric helpers."""

from __future__ import annotations


def linkage_metrics(*, total: int, matched: int) -> dict[str, float | int]:
    return {
        "total_records": total,
        "matched_records": matched,
        "unmatched_records": total - matched,
        "match_rate": 0.0 if total == 0 else round(matched / total, 6),
    }
