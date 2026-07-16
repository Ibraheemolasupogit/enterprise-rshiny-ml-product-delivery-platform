"""Governed logical-view source loading for features."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from ml_product.features.config import FeatureConfig
from ml_product.ingestion.config import DatabaseConfig
from ml_product.ingestion.local_view_client import LocalDuckDBViewClient


@dataclass(frozen=True)
class SourceDataset:
    frame: pd.DataFrame
    columns: list[str]
    provider_info: dict[str, Any]
    lineage: list[str]
    source_fingerprint: str
    database_build_identifier: str


def load_source(
    config: FeatureConfig,
    *,
    database_config_path: Path | None = None,
    database_path: Path | None = None,
) -> SourceDataset:
    db_config = DatabaseConfig.from_file(config.resolved_database_config(database_config_path))
    if database_path is not None:
        db_config = db_config.with_overrides(database_path=database_path)
    client = LocalDuckDBViewClient(
        db_config.database_path(),
        default_limit=db_config.logical_layer.max_limit,
        max_limit=db_config.logical_layer.max_limit,
    )
    description = client.describe_view(config.source.view)
    rows = client.query_view(config.source.view, limit=db_config.logical_layer.max_limit)
    frame = pd.DataFrame(rows, columns=description["columns"])
    required = set(config.identifiers)
    required.add(config.prediction_contract.target_column)
    source_predictors = [
        feature
        for feature in config.features.predictors
        if feature not in set(config.features.temporal_derivations)
    ]
    required.update(source_predictors)
    required.update(
        [
            config.eligibility.flag_column,
            config.eligibility.exclusion_reason_column,
            "admission_datetime",
            "build_identifier",
            "dataset_version",
        ]
    )
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Governed source view is missing required columns: {missing}")
    if config.source.provider != client.provider_info()["provider"]:
        raise ValueError("Feature source provider does not match governed logical-view client.")
    build_identifier = _single_value(frame, "build_identifier") or "unknown"
    return SourceDataset(
        frame=frame,
        columns=list(description["columns"]),
        provider_info=client.provider_info(),
        lineage=client.get_lineage(config.source.view),
        source_fingerprint=_fingerprint_frame(frame),
        database_build_identifier=str(build_identifier),
    )


def _single_value(frame: pd.DataFrame, column: str) -> Any:
    values = [value for value in frame[column].dropna().unique().tolist()]
    if len(values) == 1:
        return values[0]
    return None


def _fingerprint_frame(frame: pd.DataFrame) -> str:
    normalised = frame.sort_values(["admission_datetime", "admission_id"]).reset_index(drop=True)
    payload = normalised.to_json(orient="split", date_format="iso", default_handler=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
