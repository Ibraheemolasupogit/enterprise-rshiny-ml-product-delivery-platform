"""Safe filesystem storage for local registry metadata and artefacts."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from ml_product.registry.metadata import sha256_file
from ml_product.registry.models import RegistryRecord
from ml_product.registry.writers import write_json


def ensure_within_root(root: Path, path: Path) -> Path:
    resolved_root = root.resolve()
    resolved = (root / path).resolve() if not path.is_absolute() else path.resolve()
    if resolved_root != resolved and resolved_root not in resolved.parents:
        raise ValueError(f"Unsafe path escapes repository root: {path}")
    if resolved.is_symlink():
        raise ValueError(f"Symlink paths are not allowed: {path}")
    return resolved


def load_registry(path: Path) -> RegistryRecord:
    if not path.is_file():
        return RegistryRecord(version=1, registry_type="local_filesystem")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Registry metadata must contain a JSON object.")
    return RegistryRecord.model_validate(payload)


def save_registry(path: Path, record: RegistryRecord) -> None:
    write_json(path, record.model_dump(mode="json"))


def copy_immutable(source: Path, destination: Path) -> str:
    if not source.is_file():
        raise FileNotFoundError(source)
    if destination.exists():
        raise FileExistsError(f"Immutable artefact already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    shutil.copy2(source, tmp)
    tmp.replace(destination)
    return sha256_file(destination)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload
