from pathlib import Path

import pandas as pd

from ml_product.synthetic_data.config import SyntheticDataConfig
from ml_product.synthetic_data.generator import generate_synthetic_data


def test_generation_pipeline_writes_all_outputs(tmp_path: Path) -> None:
    config = SyntheticDataConfig.from_file(Path("config/synthetic_data.yaml")).with_overrides(
        output_dir=tmp_path,
        overwrite=True,
    )

    result = generate_synthetic_data(config)

    for dataset in (
        "patients",
        "admissions",
        "diagnoses",
        "ward_capacity",
        "workforce",
        "outcomes",
    ):
        assert (tmp_path / f"{dataset}.csv").is_file()
        assert (tmp_path / f"{dataset}.parquet").is_file()
        csv_frame = pd.read_csv(tmp_path / f"{dataset}.csv")
        parquet_frame = pd.read_parquet(tmp_path / f"{dataset}.parquet")
        assert list(csv_frame.columns) == list(parquet_frame.columns)

    assert result.manifest["configuration_fingerprint"] == config.fingerprint()
    assert (tmp_path / "generation_manifest.json").is_file()
    assert (tmp_path / "data_quality_issues.json").is_file()
    assert (tmp_path / "dataset_summary.json").is_file()
