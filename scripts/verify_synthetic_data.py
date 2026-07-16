"""Verify semantic reproducibility of committed synthetic sample data."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

from ml_product.synthetic_data.config import SyntheticDataConfig
from ml_product.synthetic_data.generator import generate_synthetic_data
from ml_product.synthetic_data.validation import DATASET_COLUMNS

ROOT = Path(__file__).resolve().parents[1]


def _load_csv_tables(directory: Path) -> dict[str, pd.DataFrame]:
    return {
        dataset: pd.read_csv(directory / f"{dataset}.csv", keep_default_na=False, na_values=[""])[
            columns
        ].sort_values(columns)
        for dataset, columns in DATASET_COLUMNS.items()
    }


def _stable_manifest(path: Path) -> dict[str, object]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    return {
        "dataset_version": manifest["dataset_version"],
        "seed": manifest["seed"],
        "mode": manifest["mode"],
        "configuration_fingerprint": manifest["configuration_fingerprint"],
        "datasets": manifest["datasets"],
        "issue_counts_by_type": manifest["issue_counts_by_type"],
        "total_issue_count": manifest["total_issue_count"],
        "synthetic_data_declaration": manifest["synthetic_data_declaration"],
    }


def main() -> int:
    config = SyntheticDataConfig.from_file(ROOT / "config" / "synthetic_data.yaml")
    committed_dir = config.output_directory()
    with tempfile.TemporaryDirectory() as temporary_directory:
        temp_dir = Path(temporary_directory)
        temp_config = config.with_overrides(output_dir=temp_dir, overwrite=True)
        generate_synthetic_data(temp_config)

        committed_tables = _load_csv_tables(committed_dir)
        regenerated_tables = _load_csv_tables(temp_dir)
        for dataset, committed in committed_tables.items():
            pd.testing.assert_frame_equal(
                committed.reset_index(drop=True),
                regenerated_tables[dataset].reset_index(drop=True),
                check_dtype=False,
            )

        if _stable_manifest(committed_dir / "generation_manifest.json") != _stable_manifest(
            temp_dir / "generation_manifest.json"
        ):
            raise AssertionError("Stable manifest content differs for same-seed regeneration")

    print("Synthetic sample reproducibility verification passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Synthetic reproducibility verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
