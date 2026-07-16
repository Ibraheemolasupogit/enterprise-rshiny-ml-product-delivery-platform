from ml_product.synthetic_data.validation import DATASET_COLUMNS


def test_data_dictionary_covers_all_fields() -> None:
    dictionary = open("docs/data_dictionary.md", encoding="utf-8").read()

    for dataset, columns in DATASET_COLUMNS.items():
        assert f"## {dataset}" in dictionary
        for column in columns:
            assert f"| {column} |" in dictionary
