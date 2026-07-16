"""Release version and revision helpers."""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path


def project_version(root: Path) -> str:
    payload = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    project = payload.get("project", {})
    version = project.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("pyproject.toml must define project.version.")
    return version


def git_revision(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "uncommitted"
    revision = result.stdout.strip()
    return revision if revision else "uncommitted"


def release_tag(version: str, revision: str) -> str:
    suffix = "uncommitted" if revision == "uncommitted" else revision[:12]
    return f"{version}-{suffix}"
