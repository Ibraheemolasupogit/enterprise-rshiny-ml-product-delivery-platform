"""Writers for feature matrices, targets, identifiers, and evidence."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd


def ensure_output_directory(path: Path, *, replace: bool) -> None:
    if path.exists() and any(path.iterdir()) and not replace:
        raise FileExistsError(f"Output directory is not empty: {path}")
    path.mkdir(parents=True, exist_ok=True)


def write_dataset(frame: pd.DataFrame, path_base: Path, formats: Sequence[str]) -> dict[str, Path]:
    written: dict[str, Path] = {}
    if "parquet" in formats:
        parquet_path = path_base.with_suffix(".parquet")
        frame.to_parquet(parquet_path, index=False)
        written["parquet"] = parquet_path
    if "csv" in formats:
        csv_path = path_base.with_suffix(".csv")
        frame.to_csv(csv_path, index=False)
        written["csv"] = csv_path
    return written


def write_json(path: Path, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def write_markdown_report(
    path: Path, manifest: dict[str, Any], split_summary: dict[str, Any]
) -> None:
    lines = [
        "# Feature Build Report",
        "",
        f"Feature build identifier: `{manifest['feature_build_identifier']}`",
        f"Source view: `{manifest['source_view']}`",
        f"Prediction point: `{manifest['prediction_point']}`",
        f"Target: `{manifest['target_column']}`",
        "",
        "## Split Summary",
        "",
    ]
    for split, summary in split_summary["splits"].items():
        lines.append(
            f"- {split}: {summary['row_count']} rows, {summary['patient_count']} patients, "
            f"positive_rate={summary['positive_rate']}"
        )
    lines.extend(
        [
            "",
            "## Leakage",
            "",
            "The committed leakage report records zero target, temporal, identifier, "
            "and group leakage violations.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
