"""Repository path helpers."""

from __future__ import annotations

from pathlib import Path


def repository_root() -> Path:
    """Return the repository root by walking up from this file."""

    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not locate repository root.")


def resolve_from_root(*parts: str) -> Path:
    """Resolve a path under the repository root."""

    return repository_root() / Path(*parts)
