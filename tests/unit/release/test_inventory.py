from pathlib import Path

from ml_product.release.inventory import is_releasable_path, release_inventory


def test_release_inventory_excludes_generated_outputs() -> None:
    assert not is_releasable_path(Path("data/processed/features/train_features.parquet"))
    assert not is_releasable_path(Path("models/candidate/xgboost.json"))
    assert not is_releasable_path(Path(".env"))
    assert is_releasable_path(Path("models/registry.json"))
    assert is_releasable_path(Path("src/ml_product/release/config.py"))


def test_release_inventory_has_no_generated_data_in_eligible_files() -> None:
    inventory = release_inventory(Path("."))
    files = inventory["eligible_files"]
    assert all(
        not item.startswith("data/processed/") or item.endswith(".gitkeep") for item in files
    )
    assert all(
        not item.startswith("models/candidate/") or item.endswith(".gitkeep") for item in files
    )
    assert inventory["generated_data_excluded"] is True
