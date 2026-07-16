import pandas as pd

from ml_product.synthetic_data.validation import DATASET_COLUMNS


def test_committed_sample_schemas_match_contracts() -> None:
    for dataset, columns in DATASET_COLUMNS.items():
        frame = pd.read_csv(f"data/sample/{dataset}.csv")
        assert list(frame.columns) == columns
