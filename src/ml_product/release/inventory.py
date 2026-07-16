"""Release file inventory with generated artefact exclusions."""

from __future__ import annotations

from pathlib import Path

EXCLUDED_PARTS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "__pycache__",
    "htmlcov",
}

EXCLUDED_SUFFIXES = {
    ".coverage",
    ".duckdb",
    ".joblib",
    ".parquet",
    ".pkl",
    ".pyc",
    ".sqlite",
    ".sqlite3",
}

EXCLUDED_PREFIXES = (
    "data/processed/",
    "data/raw/",
    "data/staged/",
    "data/monitoring/",
    "models/candidate/",
    "models/approved/",
    "models/archived/",
    "renv/library/",
    "renv/cache/",
)

ALWAYS_INCLUDE = {
    "data/processed/.gitkeep",
    "data/raw/.gitkeep",
    "data/staged/.gitkeep",
    "data/monitoring/.gitkeep",
    "models/candidate/.gitkeep",
    "models/approved/.gitkeep",
    "models/archived/.gitkeep",
}


def is_releasable_path(path: Path) -> bool:
    text = path.as_posix()
    if text in ALWAYS_INCLUDE:
        return True
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return False
    if path.name.startswith(".coverage"):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if any(text.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    if path.name == ".env" or path.name.endswith(".key") or path.name.endswith(".pem"):
        return False
    return True


def release_inventory(root: Path) -> dict[str, object]:
    files: list[str] = []
    excluded: list[str] = []
    for candidate in sorted(root.rglob("*")):
        if not candidate.is_file():
            continue
        relative = candidate.relative_to(root)
        if is_releasable_path(relative):
            files.append(relative.as_posix())
        else:
            excluded.append(relative.as_posix())
    return {
        "eligible_file_count": len(files),
        "excluded_file_count": len(excluded),
        "eligible_files": files,
        "excluded_examples": excluded[:50],
        "generated_data_excluded": all(
            not item.startswith(("data/processed/", "models/candidate/"))
            or item.endswith(".gitkeep")
            for item in files
        ),
    }
