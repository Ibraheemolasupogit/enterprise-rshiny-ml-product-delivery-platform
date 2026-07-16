"""Eligibility and exclusion tracking for feature builds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import pandas as pd

from ml_product.features.config import FeatureConfig


@dataclass(frozen=True)
class EligibilityResult:
    eligible: pd.DataFrame
    exclusions: pd.DataFrame
    summary: dict[str, Any]


def apply_eligibility(frame: pd.DataFrame, config: FeatureConfig) -> EligibilityResult:
    reasons: list[list[str]] = []
    target = config.prediction_contract.target_column
    for _, row in frame.iterrows():
        row_reasons: list[str] = []
        if not bool(row[config.eligibility.flag_column]):
            configured_reason = row.get(config.eligibility.exclusion_reason_column)
            row_reasons.append(str(configured_reason or "governed_ineligible"))
        if pd.isna(row[target]):
            row_reasons.append("missing_target")
        if config.eligibility.require_operational_context and not bool(
            row.get("operational_context_available", False)
        ):
            row_reasons.append("missing_operational_context")
        reasons.append(row_reasons)

    working = frame.copy()
    duplicate_mask = working["admission_id"].duplicated(keep=False)
    for index in working.index[duplicate_mask]:
        position = cast(int, working.index.get_loc(index))
        reasons[position].append("duplicate_admission_id")

    primary_reasons = [row_reasons[0] if row_reasons else "" for row_reasons in reasons]
    working["_primary_exclusion_reason"] = primary_reasons
    working["_all_exclusion_reasons"] = [";".join(row_reasons) for row_reasons in reasons]
    eligible = working[working["_primary_exclusion_reason"] == ""].copy()
    excluded = working[working["_primary_exclusion_reason"] != ""].copy()
    exclusions = excluded[
        ["admission_id", "patient_id", "_primary_exclusion_reason", "_all_exclusion_reasons"]
    ].rename(
        columns={
            "_primary_exclusion_reason": "primary_exclusion_reason",
            "_all_exclusion_reasons": "all_exclusion_reasons",
        }
    )
    counts = exclusions["primary_exclusion_reason"].value_counts().sort_index().to_dict()
    summary = {
        "source_count": int(len(frame)),
        "eligible_count": int(len(eligible)),
        "excluded_count": int(len(exclusions)),
        "exclusion_reason_counts": {str(key): int(value) for key, value in counts.items()},
        "duplicate_admission_count": int(duplicate_mask.sum()),
    }
    return EligibilityResult(
        eligible=eligible.drop(columns=["_primary_exclusion_reason", "_all_exclusion_reasons"]),
        exclusions=exclusions,
        summary=summary,
    )
