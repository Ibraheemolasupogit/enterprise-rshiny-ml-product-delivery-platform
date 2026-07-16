"""Synthetic source-system generation orchestration."""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from ml_product.synthetic_data.admissions import generate_admissions
from ml_product.synthetic_data.config import SyntheticDataConfig
from ml_product.synthetic_data.diagnoses import generate_diagnoses
from ml_product.synthetic_data.metadata import (
    build_generation_manifest,
    dataset_summary,
    file_checksum,
    manifest_path,
)
from ml_product.synthetic_data.outcomes import generate_outcomes
from ml_product.synthetic_data.patients import generate_patients
from ml_product.synthetic_data.quality_injection import apply_quality_issues
from ml_product.synthetic_data.validation import validate_tables
from ml_product.synthetic_data.ward_capacity import generate_ward_capacity
from ml_product.synthetic_data.workforce import generate_workforce
from ml_product.synthetic_data.writers import write_dataset, write_json
from ml_product.utils.paths import repository_root


@dataclass(frozen=True)
class GenerationResult:
    output_directory: Path
    manifest: dict[str, Any]
    summary: dict[str, Any]
    issues: list[dict[str, Any]]


def _validate_safe_output(config: SyntheticDataConfig) -> None:
    output_directory = config.output_directory()
    root = repository_root().resolve()
    resolved = output_directory.resolve()
    temp_roots = {Path(tempfile.gettempdir()).resolve(), Path("/private/tmp").resolve()}
    is_repo_path = root in resolved.parents or resolved == root
    is_temp_path = any(
        temp_root in resolved.parents or resolved == temp_root for temp_root in temp_roots
    )
    if not is_repo_path and not is_temp_path:
        raise ValueError(
            f"output directory must be inside repository or system temp: {output_directory}"
        )
    if (
        output_directory.exists()
        and any(output_directory.iterdir())
        and not config.outputs.overwrite
    ):
        raise FileExistsError(
            f"output directory is not empty and overwrite is false: {output_directory}"
        )


def _prepare_output(output_directory: Path, overwrite: bool) -> None:
    if output_directory.exists() and overwrite:
        for path in output_directory.iterdir():
            if path.name == ".gitkeep":
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    output_directory.mkdir(parents=True, exist_ok=True)


def generate_tables(
    config: SyntheticDataConfig,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    seed = config.dataset.seed
    patients = generate_patients(config.counts.patients, __import__("random").Random(seed + 11))
    admissions = generate_admissions(
        patients,
        target_total=config.admissions.target_total,
        start_date=config.dataset.start_date,
        end_date=config.dataset.end_date,
        ward_count=config.counts.wards,
        rng=__import__("random").Random(seed + 22),
    )
    diagnoses = generate_diagnoses(
        admissions,
        minimum_per_admission=config.diagnoses.minimum_per_admission,
        maximum_per_admission=config.diagnoses.maximum_per_admission,
        rng=__import__("random").Random(seed + 33),
    )
    ward_capacity = generate_ward_capacity(
        ward_count=config.counts.wards,
        start_date=config.dataset.start_date,
        end_date=config.dataset.end_date,
        rng=__import__("random").Random(seed + 44),
    )
    workforce = generate_workforce(
        ward_count=config.counts.wards,
        start_date=config.dataset.start_date,
        end_date=config.dataset.end_date,
        rng=__import__("random").Random(seed + 55),
    )
    patients_by_id = {row["patient_id"]: row for row in patients}
    capacity_by_ward_date = {(row["ward_id"], row["record_date"]): row for row in ward_capacity}
    workforce_by_ward_date = {(row["ward_id"], row["record_date"]): row for row in workforce}
    outcomes = generate_outcomes(
        admissions,
        patients_by_id,
        diagnoses,
        capacity_by_ward_date,
        workforce_by_ward_date,
        __import__("random").Random(seed + 66),
    )
    tables = {
        "patients": patients,
        "admissions": admissions,
        "diagnoses": diagnoses,
        "ward_capacity": ward_capacity,
        "workforce": workforce,
        "outcomes": outcomes,
    }
    clean_errors = validate_tables(tables, [])
    if clean_errors:
        raise ValueError("clean synthetic generation failed validation: " + "; ".join(clean_errors))
    issues: list[dict[str, Any]] = []
    if config.quality_issues.enabled:
        issues = apply_quality_issues(tables, config.quality_issues.rates, seed=seed)
    validation_errors = validate_tables(tables, issues)
    if validation_errors:
        raise ValueError("synthetic data validation failed: " + "; ".join(validation_errors))
    return tables, issues


def generate_synthetic_data(config: SyntheticDataConfig) -> GenerationResult:
    _validate_safe_output(config)
    output_directory = config.output_directory()
    _prepare_output(output_directory, config.outputs.overwrite)
    tables, issues = generate_tables(config)
    files = {
        dataset: write_dataset(dataset, rows, output_directory, config.outputs.formats)
        for dataset, rows in tables.items()
    }
    write_json(output_directory / "data_quality_issues.json", issues)
    summary = dataset_summary(tables, issues)
    write_json(output_directory / "dataset_summary.json", summary)
    manifest = build_generation_manifest(config=config, tables=tables, issues=issues, files=files)
    for name in ("data_quality_issues.json", "dataset_summary.json"):
        path = output_directory / name
        manifest.setdefault("files", {})[name] = {
            "json": {
                "path": manifest_path(path),
                "checksum_sha256": file_checksum(path),
                "bytes": path.stat().st_size,
            }
        }
    write_json(output_directory / "generation_manifest.json", manifest)
    return GenerationResult(output_directory, manifest, summary, issues)


def semantic_tables(directory: Path) -> dict[str, pd.DataFrame]:
    from ml_product.synthetic_data.validation import DATASET_COLUMNS

    return {
        dataset: pd.read_csv(directory / f"{dataset}.csv", keep_default_na=False, na_values=[""])[
            columns
        ]
        for dataset, columns in DATASET_COLUMNS.items()
    }
