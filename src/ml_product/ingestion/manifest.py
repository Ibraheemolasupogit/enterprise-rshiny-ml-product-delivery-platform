"""Manifest and checksum validation for database builds."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ml_product.synthetic_data.validation import DATASET_COLUMNS


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def load_json_any(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_source_manifest(source_dir: Path, *, preferred_format: str) -> dict[str, Any]:
    manifest = load_json(source_dir / "generation_manifest.json")
    for dataset in DATASET_COLUMNS:
        dataset_files = manifest.get("files", {}).get(dataset, {})
        file_meta = dataset_files.get(preferred_format) or dataset_files.get("csv")
        if not isinstance(file_meta, dict):
            raise ValueError(f"Manifest missing {preferred_format}/csv metadata for {dataset}")
        path = source_dir / f"{dataset}.{preferred_format}"
        if not path.exists():
            path = source_dir / f"{dataset}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing source file for {dataset}: {path}")
        expected = file_meta.get("checksum_sha256")
        actual = sha256_file(path)
        if expected != actual:
            raise ValueError(
                f"Checksum mismatch for {path.name}: expected {expected}, got {actual}"
            )
    return manifest


def build_identifier(source_fingerprint: str, config_version: str) -> str:
    payload = f"{source_fingerprint}|{config_version}|duckdb-local-v1".encode()
    return "DBUILD-" + hashlib.sha256(payload).hexdigest()[:16]
