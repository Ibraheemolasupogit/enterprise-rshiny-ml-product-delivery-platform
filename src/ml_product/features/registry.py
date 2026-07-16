"""Feature registry generation."""

from __future__ import annotations

from typing import Any

from ml_product.features.config import FeatureConfig
from ml_product.features.transformers import Preprocessor


def build_feature_registry(config: FeatureConfig, preprocessor: Preprocessor) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for column in config.features.numeric:
        if config.missingness.add_missing_indicators:
            entries.append(_entry(f"{column}__missing", column, "missing_indicator"))
        entries.append(_entry(column, column, "median_impute_standard_scale"))
    for column in config.features.boolean:
        if config.missingness.add_missing_indicators:
            entries.append(_entry(f"{column}__missing", column, "missing_indicator"))
        entries.append(_entry(column, column, "mode_impute_boolean_to_integer"))
    for column, levels in preprocessor.categorical_levels.items():
        if config.missingness.add_missing_indicators:
            entries.append(_entry(f"{column}__missing", column, "missing_indicator"))
        for level in levels:
            entries.append(
                {
                    "feature_name": _one_hot_name(column, level),
                    "source_column": column,
                    "feature_group": "categorical",
                    "transformation": "explicit_missing_one_hot",
                    "prediction_time_available": True,
                    "leakage_status": "permitted",
                }
            )
    ordered = [
        entry
        for name in preprocessor.output_columns
        for entry in entries
        if entry["feature_name"] == name
    ]
    return {
        "version": config.version,
        "registry_entry_count": len(ordered),
        "output_feature_count": len(preprocessor.output_columns),
        "coverage_valid": len(ordered) == len(preprocessor.output_columns),
        "stable_ordering_valid": [entry["feature_name"] for entry in ordered]
        == preprocessor.output_columns,
        "features": ordered,
    }


def _entry(feature_name: str, source_column: str, transformation: str) -> dict[str, Any]:
    return {
        "feature_name": feature_name,
        "source_column": source_column,
        "feature_group": "derived" if feature_name.endswith("__missing") else "predictor",
        "transformation": transformation,
        "prediction_time_available": True,
        "leakage_status": "permitted",
    }


def _one_hot_name(column: str, level: str) -> str:
    safe = level.lower().replace(" ", "_").replace("/", "_").replace("-", "_")
    safe = "".join(
        character if character.isalnum() or character == "_" else "_" for character in safe
    )
    return f"{column}__{safe}"
