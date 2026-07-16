"""Metadata and fingerprint helpers for model-development evidence."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from ml_product.modelling.config import ModelTrainingConfig, ThresholdConfig


def config_fingerprint(config: ModelTrainingConfig, thresholds: ThresholdConfig) -> str:
    payload = {
        "model_training": config.model_dump(mode="json"),
        "model_thresholds": thresholds.model_dump(mode="json"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def semantic_model_identifier(
    model_family: str, feature_build_identifier: str, training_fingerprint: str
) -> str:
    payload = f"{model_family}|{feature_build_identifier}|{training_fingerprint}"
    return "CAND-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16].upper()


def timestamp_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def stable_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "generated_at_utc"}
