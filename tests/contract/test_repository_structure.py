from pathlib import Path

from scripts.validate_repository import (
    PROHIBITED_ARTIFACT_SUFFIXES,
    REQUIRED_DIRECTORIES,
    REQUIRED_DOCS,
    REQUIRED_ROOT_FILES,
    validate_boundaries,
    validate_config,
    validate_docs,
    validate_structure,
)


def test_required_root_files_exist() -> None:
    for file_name in REQUIRED_ROOT_FILES:
        assert Path(file_name).is_file(), file_name


def test_required_directories_exist() -> None:
    for directory in REQUIRED_DIRECTORIES:
        assert Path(directory).is_dir(), directory


def test_required_documentation_exists() -> None:
    for document in REQUIRED_DOCS:
        assert Path(document).is_file(), document


def test_repository_validation_checks_pass() -> None:
    assert validate_structure() == []
    assert validate_config() == []
    assert validate_docs() == []
    assert validate_boundaries() == []


def test_no_generated_model_dataset_or_database_artifacts_committed() -> None:
    ignored_parts = {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "htmlcov"}
    ignored_prefixes = {("renv", "library"), ("renv", "cache")}
    for path in Path.cwd().rglob("*"):
        relative = path.relative_to(Path.cwd())
        if (
            ignored_parts.intersection(relative.parts)
            or tuple(relative.parts[:2]) in ignored_prefixes
            or not path.is_file()
        ):
            continue
        if relative.parts[:2] == ("data", "sample") and path.suffix == ".parquet":
            continue
        if relative.parts[:3] == ("data", "processed", "features") and path.suffix in {
            ".parquet",
            ".csv",
            ".json",
        }:
            continue
        if relative.parts[:2] == ("models", "candidate") and path.suffix in {
            ".joblib",
            ".json",
        }:
            continue
        if relative.parts[:2] == ("models", "registered") and path.suffix in {
            ".joblib",
            ".json",
        }:
            continue
        assert path.suffix.lower() not in PROHIBITED_ARTIFACT_SUFFIXES, path
