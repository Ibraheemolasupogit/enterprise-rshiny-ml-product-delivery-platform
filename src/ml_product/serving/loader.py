"""Load registry model artefacts for serving."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib

from ml_product.registry.config import GovernanceConfig, RegistryConfig
from ml_product.registry.models import ModelVersion
from ml_product.registry.registry import LocalModelRegistry
from ml_product.serving.config import ServingConfig


@dataclass(frozen=True)
class LoadedModel:
    version: ModelVersion
    model: Any
    calibrator: Any
    preprocessor_metadata: dict[str, Any]
    feature_importance: dict[str, Any]
    review_mode: bool


def resolve_model(
    *,
    registry_config: RegistryConfig,
    governance_config: GovernanceConfig,
    serving_config: ServingConfig,
    root: Path = Path("."),
) -> LoadedModel | None:
    registry = LocalModelRegistry(registry_config, governance_config, root=root)
    review_mode = _review_mode_enabled(serving_config)
    if review_mode and serving_config.service.environment != "local":
        raise ValueError("Review mode is only allowed in the local environment.")
    version = registry.get_active_model()
    if version is None and review_mode:
        versions = registry.list_models()
        version = versions[-1] if versions else None
    if version is None:
        return None
    if not review_mode and version.status != "active":
        return None
    return load_version(version, review_mode=review_mode, root=root)


def load_version(
    version: ModelVersion, *, review_mode: bool, root: Path = Path(".")
) -> LoadedModel:
    from xgboost import XGBClassifier

    model = XGBClassifier()
    model.load_model(root / version.artefacts.model_path)
    calibrator = joblib.load(root / version.artefacts.calibrator_path)
    preprocessor = json.loads(
        (root / "reports/model_evaluation/preprocessor_metadata.json").read_text(encoding="utf-8")
    )
    feature_importance = json.loads(
        (root / "reports/model_evaluation/feature_importance.json").read_text(encoding="utf-8")
    )
    if (
        preprocessor["semantic_fingerprint"]
        != version.preprocessor_contract.preprocessor_fingerprint
    ):
        raise ValueError("Preprocessor fingerprint mismatch.")
    if preprocessor["output_feature_names"] != version.feature_contract.feature_names:
        raise ValueError("Feature schema mismatch.")
    return LoadedModel(
        version=version,
        model=model,
        calibrator=calibrator,
        preprocessor_metadata=preprocessor,
        feature_importance=feature_importance,
        review_mode=review_mode,
    )


def _review_mode_enabled(config: ServingConfig) -> bool:
    return os.environ.get("SERVING_REVIEW_MODE", "").lower() == "true"
