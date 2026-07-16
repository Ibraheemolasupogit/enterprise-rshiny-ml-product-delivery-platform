"""Stable metadata helpers for feature builds."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from ml_product.features.config import FeatureConfig


def config_fingerprint(config: FeatureConfig) -> str:
    payload = config.model_dump(mode="json")
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def frame_fingerprint(frame: pd.DataFrame) -> str:
    payload = frame.to_json(orient="split", date_format="iso", default_handler=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_identifier(source_fingerprint: str, config_hash: str, split_fingerprint: str) -> str:
    payload = f"{source_fingerprint}|{config_hash}|{split_fingerprint}"
    return "FBUILD-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def manifest_payload(
    *,
    config: FeatureConfig,
    source_fingerprint: str,
    database_build_identifier: str,
    split_fingerprint: str,
    output_checksums: dict[str, str],
    counts: dict[str, Any],
) -> dict[str, Any]:
    config_hash = config_fingerprint(config)
    return {
        "feature_build_identifier": build_identifier(
            source_fingerprint, config_hash, split_fingerprint
        ),
        "dataset_version": config.version,
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source_view": config.source.view,
        "source_provider": config.source.provider,
        "source_fingerprint": source_fingerprint,
        "database_build_identifier": database_build_identifier,
        "feature_configuration_fingerprint": config_hash,
        "split_fingerprint": split_fingerprint,
        "prediction_point": config.prediction_contract.prediction_point,
        "target_column": config.prediction_contract.target_column,
        "output_checksums": output_checksums,
        "counts": counts,
    }


def stable_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "generated_at_utc"}


def contains_absolute_user_path(path: Path) -> bool:
    return "/Users/" in path.read_text(encoding="utf-8", errors="ignore")
