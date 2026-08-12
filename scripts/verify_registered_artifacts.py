"""Verify registered model artefacts are present and match registry metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _registered_version(registry: dict[str, Any], version: int) -> dict[str, Any]:
    for model in registry.get("models", []):
        if not isinstance(model, dict):
            continue
        for candidate in model.get("versions", []):
            if isinstance(candidate, dict) and candidate.get("registry_version") == version:
                return candidate
    raise ValueError(f"Registry version v{version:06d} is not recorded.")


def verify_registered_artifacts(root: Path, version: int) -> None:
    registry_path = root / "models" / "registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registered = _registered_version(registry, version)
    artefacts = registered["artefacts"]
    checks = (
        ("model_path", "model_sha256"),
        ("calibrator_path", "calibrator_sha256"),
    )
    for path_key, checksum_key in checks:
        path = root / artefacts[path_key]
        if not path.is_file():
            raise FileNotFoundError(f"Missing registered artefact: {path}")
        observed = _sha256(path)
        expected = artefacts[checksum_key]
        if observed != expected:
            raise ValueError(
                f"Checksum mismatch for {path}: expected {expected}, observed {observed}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--version", type=int, default=1)
    args = parser.parse_args()
    verify_registered_artifacts(args.root, args.version)


if __name__ == "__main__":
    main()
