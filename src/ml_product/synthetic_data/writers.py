"""Stable writers for synthetic source datasets."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from ml_product.synthetic_data.validation import DATASET_COLUMNS


def _atomic_replace_bytes(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
        handle.write(data)
        temp_name = handle.name
    os.replace(temp_name, target)


def _atomic_replace_text(target: Path, text: str) -> None:
    _atomic_replace_bytes(target, text.encode("utf-8"))


def frame_for_dataset(dataset: str, rows: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=DATASET_COLUMNS[dataset])
    return frame.sort_values(DATASET_COLUMNS[dataset]).reset_index(drop=True)


def write_dataset(
    dataset: str, rows: list[dict[str, Any]], directory: Path, formats: Sequence[str]
) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    frame = frame_for_dataset(dataset, rows)
    if "csv" in formats:
        csv_path = directory / f"{dataset}.csv"
        _atomic_replace_text(csv_path, frame.to_csv(index=False, lineterminator="\n"))
        paths["csv"] = csv_path
    if "parquet" in formats:
        parquet_path = directory / f"{dataset}.parquet"
        with tempfile.NamedTemporaryFile(dir=directory, delete=False) as handle:
            temp_name = handle.name
        frame.to_parquet(temp_name, index=False, engine="pyarrow")
        os.replace(temp_name, parquet_path)
        paths["parquet"] = parquet_path
    return paths


def write_json(path: Path, payload: Any) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n"
    _atomic_replace_text(path, text)
