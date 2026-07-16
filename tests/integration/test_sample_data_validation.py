from pathlib import Path

import pytest


def test_committed_sample_data_exists() -> None:
    sample_dir = Path("data/sample")
    if not (sample_dir / "generation_manifest.json").exists():
        pytest.skip("Committed sample data has not been generated yet.")

    for dataset in (
        "patients",
        "admissions",
        "diagnoses",
        "ward_capacity",
        "workforce",
        "outcomes",
    ):
        assert (sample_dir / f"{dataset}.csv").is_file()
        assert (sample_dir / f"{dataset}.parquet").is_file()
