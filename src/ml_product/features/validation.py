"""Feature-output validation."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

from ml_product.features.config import FeatureConfig
from ml_product.features.leakage import check_leakage


def validate_feature_outputs(
    config: FeatureConfig,
    *,
    output_dir: Path | None = None,
    evidence_dir: Path | None = None,
) -> dict[str, Any]:
    resolved_output = config.resolved_output_directory(output_dir)
    resolved_evidence = evidence_dir or config.resolved_evidence_directory()
    errors: list[str] = []
    features: dict[str, pd.DataFrame] = {}
    targets: dict[str, pd.DataFrame] = {}
    identifiers: dict[str, pd.DataFrame] = {}
    for split in ("train", "validation", "test"):
        for kind, store in (
            ("features", features),
            ("target", targets),
            ("identifiers", identifiers),
        ):
            path = resolved_output / f"{split}_{kind}.parquet"
            if not path.is_file():
                errors.append(f"Missing output: {path.name}")
                continue
            store[split] = pd.read_parquet(path)
    if len(features) == 3:
        columns = list(features["train"].columns)
        for split, frame in features.items():
            if list(frame.columns) != columns:
                errors.append(f"{split} feature columns differ from training columns.")
            if frame.isna().any().any():
                errors.append(f"{split} features contain missing values.")
            numeric_values = frame.select_dtypes(include=["number"])
            if not numeric_values.map(lambda value: math.isfinite(float(value))).all().all():
                errors.append(f"{split} features contain non-finite numeric values.")
            if any(column.startswith("index") for column in frame.columns):
                errors.append(f"{split} features contain an index-like leakage column.")
    if len(targets) == 3 and len(identifiers) == 3:
        for split in ("train", "validation", "test"):
            if len(targets[split]) != len(identifiers[split]) or len(targets[split]) != len(
                features[split]
            ):
                errors.append(f"{split} features, target, and identifiers are not row-aligned.")
    leakage = check_leakage(config)
    if not leakage.valid:
        errors.append("Configured predictors fail leakage checks.")
    required_evidence = [
        "feature_build_manifest.json",
        "feature_registry.json",
        "split_summary.json",
        "exclusion_summary.json",
        "leakage_report.json",
        "preprocessor_metadata.json",
        "feature_build_report.md",
    ]
    for name in required_evidence:
        if not (resolved_evidence / name).is_file():
            errors.append(f"Missing evidence file: {name}")
    train_features = features.get("train")
    feature_column_count = 0 if train_features is None else len(train_features.columns)
    return {
        "valid": not errors,
        "errors": errors,
        "feature_column_count": feature_column_count,
    }
