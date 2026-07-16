from ml_product.utils.paths import repository_root, resolve_from_root


def test_repository_root_contains_project_files() -> None:
    root = repository_root()

    assert (root / "pyproject.toml").is_file()
    assert (root / ".git").exists()


def test_resolve_from_root() -> None:
    assert resolve_from_root("config", "settings.yaml").is_file()
