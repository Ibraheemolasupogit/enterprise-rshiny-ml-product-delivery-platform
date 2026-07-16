"""Load and validate Milestone 5 feature artefacts for modelling."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from ml_product.features.metadata import frame_fingerprint
from ml_product.modelling.config import ModelTrainingConfig

SPLITS = ("train", "validation", "test")


@dataclass(frozen=True)
class SplitData:
    features: pd.DataFrame
    target: pd.Series
    identifiers: pd.DataFrame


@dataclass(frozen=True)
class ModelData:
    splits: dict[str, SplitData]
    feature_names: list[str]
    manifest: dict[str, Any]
    registry: dict[str, Any]
    split_summary: dict[str, Any]
    leakage_report: dict[str, Any]
    preprocessor_metadata: dict[str, Any]


def load_model_data(
    config: ModelTrainingConfig,
    feature_dir: Path | None = None,
    report_dir: Path | None = None,
) -> ModelData:
    directory = config.feature_directory(feature_dir)
    report_paths = _report_paths(config, report_dir)
    manifest = _load_json(report_paths["manifest"])
    registry = _load_json(report_paths["registry"])
    split_summary = _load_json(report_paths["split_summary"])
    leakage_report = _load_json(report_paths["leakage_report"])
    preprocessor_metadata = _load_json(report_paths["preprocessor_metadata"])
    splits: dict[str, SplitData] = {}
    for split in SPLITS:
        features = pd.read_parquet(directory / f"{split}_features.parquet")
        target_frame = pd.read_parquet(directory / f"{split}_target.parquet")
        identifiers = pd.read_parquet(directory / f"{split}_identifiers.parquet")
        if "target" not in target_frame.columns:
            raise ValueError(f"{split}_target.parquet must contain a target column.")
        splits[split] = SplitData(
            features=features,
            target=target_frame["target"].astype(bool),
            identifiers=identifiers,
        )
    _validate_contract(config, splits, manifest, registry, split_summary, leakage_report)
    return ModelData(
        splits=splits,
        feature_names=list(splits["train"].features.columns),
        manifest=manifest,
        registry=registry,
        split_summary=split_summary,
        leakage_report=leakage_report,
        preprocessor_metadata=preprocessor_metadata,
    )


def _report_paths(config: ModelTrainingConfig, report_dir: Path | None = None) -> dict[str, Path]:
    base = config.report_directory(report_dir)
    return {
        "manifest": base / Path(config.feature_source.manifest).name,
        "registry": base / Path(config.feature_source.registry).name,
        "split_summary": base / Path(config.feature_source.split_summary).name,
        "leakage_report": base / Path(config.feature_source.leakage_report).name,
        "preprocessor_metadata": base / Path(config.feature_source.preprocessor_metadata).name,
    }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _validate_contract(
    config: ModelTrainingConfig,
    splits: dict[str, SplitData],
    manifest: dict[str, Any],
    registry: dict[str, Any],
    split_summary: dict[str, Any],
    leakage_report: dict[str, Any],
) -> None:
    train_columns = list(splits["train"].features.columns)
    if len(train_columns) != config.feature_source.expected_feature_count:
        raise ValueError("Feature-count mismatch for modelling inputs.")
    if registry.get("output_feature_count") != len(train_columns):
        raise ValueError("Feature registry count does not match feature outputs.")
    for split, split_data in splits.items():
        if list(split_data.features.columns) != train_columns:
            raise ValueError(f"{split} feature schema does not match training schema.")
        if len(split_data.features) != len(split_data.target):
            raise ValueError(f"{split} features and target are not row-aligned.")
        if len(split_data.features) != len(split_data.identifiers):
            raise ValueError(f"{split} features and identifiers are not row-aligned.")
        for kind, frame in (
            ("features", split_data.features),
            ("target", split_data.target.to_frame("target")),
            ("identifiers", split_data.identifiers),
        ):
            expected = manifest["output_checksums"].get(f"{split}_{kind}")
            actual = frame_fingerprint(frame)
            if expected != actual:
                raise ValueError(f"Stale feature artefact detected: {split}_{kind}.")
    if split_summary.get("patient_overlap_count") != 0:
        raise ValueError("Patient overlap detected in split summary.")
    if split_summary.get("admission_overlap_count") != 0:
        raise ValueError("Admission overlap detected in split summary.")
    if leakage_report.get("total_violations") != 0:
        raise ValueError("Feature leakage report is not clean.")
    if manifest["counts"]["final_feature_count"] != len(train_columns):
        raise ValueError("Feature manifest final_feature_count does not match outputs.")
