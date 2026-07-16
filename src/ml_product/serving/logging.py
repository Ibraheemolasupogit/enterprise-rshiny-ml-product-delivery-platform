"""Prediction event logging without sensitive payloads."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from ml_product.serving.schemas import PredictionResponse


def write_prediction_event(
    *,
    path: Path,
    response: PredictionResponse | None,
    latency_ms: float,
    success: bool,
    error_code: str | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "request_id": response.request.request_id if response else None,
        "timestamp": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "model_name": response.model.model_name if response else None,
        "registry_version": response.model.registry_version if response else None,
        "candidate_identifier": response.model.candidate_identifier if response else None,
        "model_family": response.model.model_family if response else None,
        "probability": response.prediction.long_stay_probability if response else None,
        "prediction": response.prediction.predicted_long_stay if response else None,
        "risk_band": response.prediction.risk_band if response else None,
        "latency_ms": latency_ms,
        "review_mode": response.request.review_mode if response else None,
        "input_schema_fingerprint": "raw-admission-v1",
        "success": success,
        "error_code": error_code,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
