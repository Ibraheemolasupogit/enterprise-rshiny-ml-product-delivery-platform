from pathlib import Path

import pandas as pd

from ml_product.features.writers import write_dataset


def test_writer_round_trips_parquet_and_csv(tmp_path: Path) -> None:
    frame = pd.DataFrame({"feature": [1.0, 2.0]})
    written = write_dataset(frame, tmp_path / "sample", ["parquet", "csv"])
    assert pd.read_parquet(written["parquet"]).equals(frame)
    assert pd.read_csv(written["csv"]).equals(frame)
