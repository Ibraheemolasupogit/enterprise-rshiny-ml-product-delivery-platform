"""Deterministic lifecycle registration identity helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from ml_product.lifecycle.package import ModelLifecyclePackage


def registration_fingerprint(package: ModelLifecyclePackage) -> str:
    """Build a stable registration fingerprint without wall-clock inputs."""

    payload: dict[str, Any] = {
        "model_name": package.model_name,
        "model_version": package.model_version,
        "candidate_identifier": package.candidate_identifier,
        "dataset_version": package.source.get("dataset_version"),
        "source_fingerprint": package.source.get("source_fingerprint"),
        "model_family": package.model_family,
        "prediction_point": package.target.get("prediction_point"),
        "artefact_checksums": {
            "model_sha256": package.artefacts.get("model_sha256"),
            "calibrator_sha256": package.artefacts.get("calibrator_sha256"),
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
