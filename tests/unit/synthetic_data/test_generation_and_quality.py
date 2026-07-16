from pathlib import Path

import pytest

from ml_product.synthetic_data.config import SyntheticDataConfig
from ml_product.synthetic_data.generator import generate_tables
from ml_product.synthetic_data.validation import validate_tables


def test_generation_is_deterministic_for_same_seed() -> None:
    config = SyntheticDataConfig.from_file(Path("config/synthetic_data.yaml"))

    first_tables, first_issues = generate_tables(config)
    second_tables, second_issues = generate_tables(config)

    assert first_tables == second_tables
    assert first_issues == second_issues


def test_generation_changes_for_different_seed() -> None:
    config = SyntheticDataConfig.from_file(Path("config/synthetic_data.yaml"))
    changed = config.with_overrides(seed=config.dataset.seed + 1)

    first_tables, _ = generate_tables(config)
    changed_tables, _ = generate_tables(changed)

    assert first_tables["patients"] != changed_tables["patients"]


def test_clean_mode_has_no_intentional_issues() -> None:
    config = SyntheticDataConfig.from_file(Path("config/synthetic_data.yaml")).with_overrides(
        clean=True
    )

    tables, issues = generate_tables(config)

    assert issues == []
    assert validate_tables(tables, issues) == []


def test_unexpected_issue_fails_validation() -> None:
    config = SyntheticDataConfig.from_file(Path("config/synthetic_data.yaml")).with_overrides(
        clean=True
    )
    tables, _ = generate_tables(config)
    tables["outcomes"][0]["long_stay_flag"] = not tables["outcomes"][0]["long_stay_flag"]

    errors = validate_tables(tables, [])

    assert any("long_stay_flag" in error for error in errors)


def test_invalid_output_without_overwrite_fails(tmp_path: Path) -> None:
    config = SyntheticDataConfig.from_file(Path("config/synthetic_data.yaml")).with_overrides(
        output_dir=tmp_path,
        overwrite=False,
    )
    (tmp_path / "existing.txt").write_text("occupied", encoding="utf-8")

    from ml_product.synthetic_data.generator import generate_synthetic_data

    with pytest.raises(FileExistsError):
        generate_synthetic_data(config)
