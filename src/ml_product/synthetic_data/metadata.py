"""Metadata and manifest helpers for generated synthetic datasets."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ml_product import __version__
from ml_product.synthetic_data.config import SyntheticDataConfig
from ml_product.synthetic_data.validation import DATASET_COLUMNS
from ml_product.utils.paths import repository_root

SYNTHETIC_DECLARATION = (
    "Generated synthetic operational source data only; not extracted from real systems and not for "
    "clinical or operational use."
)


def file_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_path(path: Path) -> str:
    resolved = path.resolve()
    root = repository_root().resolve()
    if resolved.is_relative_to(root):
        return resolved.relative_to(root).as_posix()
    return resolved.as_posix()


def dataset_summary(
    tables: dict[str, list[dict[str, Any]]],
    issues: list[dict[str, Any]],
) -> dict[str, Any]:
    issue_counts: dict[str, int] = {}
    for issue in issues:
        key = issue["issue_type"]
        issue_counts[key] = issue_counts.get(key, 0) + 1
    datasets = {
        name: {
            "rows": len(rows),
            "columns": len(DATASET_COLUMNS[name]),
            "column_names": DATASET_COLUMNS[name],
        }
        for name, rows in tables.items()
    }
    return {
        "synthetic_data_declaration": SYNTHETIC_DECLARATION,
        "datasets": datasets,
        "issue_counts_by_type": issue_counts,
        "total_issue_count": len(issues),
    }


def _date_bounds(values: list[str]) -> dict[str, str]:
    parsed = pd.to_datetime(pd.Series(values), format="mixed").dt.date.astype(str).tolist()
    return {"minimum": min(parsed), "maximum": max(parsed)}


def build_generation_manifest(
    *,
    config: SyntheticDataConfig,
    tables: dict[str, list[dict[str, Any]]],
    issues: list[dict[str, Any]],
    files: dict[str, dict[str, Path]],
) -> dict[str, Any]:
    manifest_files: dict[str, dict[str, dict[str, Any]]] = {}
    for dataset, format_paths in files.items():
        manifest_files[dataset] = {
            file_format: {
                "path": manifest_path(path),
                "checksum_sha256": file_checksum(path),
                "bytes": path.stat().st_size,
            }
            for file_format, path in format_paths.items()
        }

    admission_dates = pd.DataFrame(tables["admissions"])["admission_datetime"].tolist()
    ward_capacity_dates = pd.DataFrame(tables["ward_capacity"])["record_date"].tolist()
    workforce_dates = pd.DataFrame(tables["workforce"])["record_date"].tolist()
    discharge_dates = pd.DataFrame(tables["outcomes"])["discharge_datetime"].tolist()
    all_observed_dates = admission_dates + ward_capacity_dates + workforce_dates + discharge_dates

    summary = dataset_summary(tables, issues)
    return {
        "dataset_version": config.dataset.version,
        "generator_package_version": __version__,
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "seed": config.dataset.seed,
        "mode": config.dataset.mode,
        "configuration_fingerprint": config.fingerprint(),
        "synthetic_data_declaration": SYNTHETIC_DECLARATION,
        "date_ranges": {
            "configured_generation_range": {
                "minimum": config.dataset.start_date.isoformat(),
                "maximum": config.dataset.end_date.isoformat(),
            },
            "admission_date_range": _date_bounds(admission_dates),
            "ward_capacity_date_range": _date_bounds(ward_capacity_dates),
            "workforce_date_range": _date_bounds(workforce_dates),
            "discharge_date_range": _date_bounds(discharge_dates),
            "overall_observed_date_range": _date_bounds(all_observed_dates),
        },
        "date_range": _date_bounds(all_observed_dates),
        "datasets": summary["datasets"],
        "files": manifest_files,
        "issue_counts_by_type": summary["issue_counts_by_type"],
        "total_issue_count": len(issues),
        "determinism_note": (
            "Compare semantic table content and stable metadata; generated_at_utc is intentionally "
            "volatile."
        ),
    }
