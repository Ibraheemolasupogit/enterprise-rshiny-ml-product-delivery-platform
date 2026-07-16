"""Deterministic temporal patient-group dataset splitting."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import pandas as pd

from ml_product.features.config import FeatureConfig

SPLITS = ("train", "validation", "test")


@dataclass(frozen=True)
class SplitResult:
    frame: pd.DataFrame
    assignments: pd.DataFrame
    summary: dict[str, Any]
    fingerprint: str


def split_dataset(frame: pd.DataFrame, config: FeatureConfig) -> SplitResult:
    working = frame.copy()
    working["admission_datetime"] = pd.to_datetime(working["admission_datetime"], errors="raise")
    if config.splitting.group_by_patient:
        groups = (
            working.groupby("patient_id", as_index=False)
            .agg(first_admission=("admission_datetime", "min"), rows=("admission_id", "count"))
            .sort_values(["first_admission", "patient_id"], kind="mergesort")
            .reset_index(drop=True)
        )
        assignments = _assign_groups(groups, len(working), config)
        working = working.merge(assignments[["patient_id", "split"]], on="patient_id", how="left")
    else:
        working = working.sort_values(["admission_datetime", "admission_id"], kind="mergesort")
        working["split"] = _assign_rows(len(working), config)
    working = working.sort_values(["split", "admission_datetime", "admission_id"], kind="mergesort")
    assignment_frame = working[["admission_id", "patient_id", "admission_datetime", "split"]].copy()
    summary = _summarise(working, config)
    fingerprint = _split_fingerprint(assignment_frame, config)
    summary["split_fingerprint"] = fingerprint
    return SplitResult(
        frame=working.reset_index(drop=True),
        assignments=assignment_frame.reset_index(drop=True),
        summary=summary,
        fingerprint=fingerprint,
    )


def _assign_groups(groups: pd.DataFrame, total_rows: int, config: FeatureConfig) -> pd.DataFrame:
    train_cutoff = total_rows * config.splitting.train_fraction
    validation_cutoff = total_rows * (
        config.splitting.train_fraction + config.splitting.validation_fraction
    )
    cumulative = 0
    splits: list[str] = []
    for _, row in groups.iterrows():
        if cumulative < train_cutoff:
            split = "train"
        elif cumulative < validation_cutoff:
            split = "validation"
        else:
            split = "test"
        splits.append(split)
        cumulative += int(row["rows"])
    assigned = groups.copy()
    assigned["split"] = splits
    return _ensure_non_empty_patient_splits(assigned)


def _assign_rows(row_count: int, config: FeatureConfig) -> list[str]:
    train_end = max(1, int(row_count * config.splitting.train_fraction))
    validation_end = max(
        train_end + 1,
        int(row_count * (config.splitting.train_fraction + config.splitting.validation_fraction)),
    )
    validation_end = min(validation_end, row_count - 1)
    return [
        "train" if index < train_end else "validation" if index < validation_end else "test"
        for index in range(row_count)
    ]


def _ensure_non_empty_patient_splits(groups: pd.DataFrame) -> pd.DataFrame:
    if groups["split"].nunique() == 3:
        return groups
    result = groups.copy()
    if len(result) < 3:
        raise ValueError("At least three patient groups are required for three non-empty splits.")
    result.loc[result.index[-2], "split"] = "validation"
    result.loc[result.index[-1], "split"] = "test"
    return result


def _summarise(frame: pd.DataFrame, config: FeatureConfig) -> dict[str, Any]:
    target = config.prediction_contract.target_column
    split_summaries: dict[str, dict[str, Any]] = {}
    patients_by_split: dict[str, set[str]] = {}
    admissions_by_split: dict[str, set[str]] = {}
    for split in SPLITS:
        subset = frame[frame["split"] == split]
        positives = int(subset[target].astype(bool).sum()) if len(subset) else 0
        patients = {str(value) for value in subset["patient_id"].tolist()}
        admissions = {str(value) for value in subset["admission_id"].tolist()}
        patients_by_split[split] = patients
        admissions_by_split[split] = admissions
        split_summaries[split] = {
            "row_count": int(len(subset)),
            "patient_count": len(patients),
            "positive_count": positives,
            "positive_rate": round(positives / len(subset), 6) if len(subset) else 0.0,
            "minimum_admission_date": _date_or_none(subset["admission_datetime"].min()),
            "maximum_admission_date": _date_or_none(subset["admission_datetime"].max()),
        }
    patient_overlap = _overlap_count(patients_by_split)
    admission_overlap = _overlap_count(admissions_by_split)
    return {
        "strategy": "temporal_patient_group" if config.splitting.group_by_patient else "temporal",
        "seed": config.splitting.seed,
        "splits": split_summaries,
        "patient_overlap_count": patient_overlap,
        "admission_overlap_count": admission_overlap,
        "allocation_strategy": (
            "Sort patients by first admission datetime, then patient_id; allocate whole "
            "patient groups to 60/20/20 row-count targets."
        ),
    }


def _date_or_none(value: Any) -> str | None:
    if pd.isna(value):
        return None
    return pd.Timestamp(value).date().isoformat()


def _overlap_count(values: dict[str, set[str]]) -> int:
    overlap: set[str] = set()
    split_names = list(values)
    for index, left in enumerate(split_names):
        for right in split_names[index + 1 :]:
            overlap.update(values[left].intersection(values[right]))
    return len(overlap)


def _split_fingerprint(assignments: pd.DataFrame, config: FeatureConfig) -> str:
    payload = {
        "assignments": assignments.assign(
            admission_datetime=assignments["admission_datetime"].astype(str)
        ).to_dict(orient="records"),
        "strategy": config.splitting.model_dump(),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
