"""Orchestrate Milestone 5 feature dataset builds."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ml_product.features.config import FeatureConfig
from ml_product.features.eligibility import apply_eligibility
from ml_product.features.leakage import assert_no_leakage
from ml_product.features.metadata import frame_fingerprint, manifest_payload
from ml_product.features.registry import build_feature_registry
from ml_product.features.source import load_source
from ml_product.features.splitting import SPLITS, split_dataset
from ml_product.features.temporal import add_temporal_features
from ml_product.features.transformers import fit_preprocessor
from ml_product.features.writers import (
    ensure_output_directory,
    write_dataset,
    write_json,
    write_markdown_report,
)


@dataclass(frozen=True)
class FeatureBuildResult:
    manifest: dict[str, Any]
    split_summary: dict[str, Any]
    feature_registry: dict[str, Any]
    leakage_report: dict[str, Any]
    exclusion_summary: dict[str, Any]
    preprocessor_metadata: dict[str, Any]
    output_directory: Path
    evidence_directory: Path


def build_features(
    config: FeatureConfig,
    *,
    database_config_path: Path | None = None,
    database_path: Path | None = None,
    output_dir: Path | None = None,
    evidence_dir: Path | None = None,
    replace: bool = False,
) -> FeatureBuildResult:
    output_directory = config.resolved_output_directory(output_dir)
    evidence_directory = (
        config.resolved_evidence_directory()
        if evidence_dir is None
        else config.resolved_output_directory(evidence_dir)
    )
    ensure_output_directory(output_directory, replace=replace)
    evidence_directory.mkdir(parents=True, exist_ok=True)

    leakage = assert_no_leakage(config)
    source = load_source(
        config,
        database_config_path=database_config_path,
        database_path=database_path,
    )
    temporal = add_temporal_features(source.frame)
    eligibility = apply_eligibility(temporal, config)
    split = split_dataset(eligibility.eligible, config)
    split_frames = {
        name: split.frame[split.frame["split"] == name].reset_index(drop=True) for name in SPLITS
    }
    preprocessor = fit_preprocessor(split_frames["train"], config)
    transformed = {
        name: preprocessor.transform(frame, config) for name, frame in split_frames.items()
    }
    output_checksums: dict[str, str] = {}
    for name, frame in transformed.items():
        target = split_frames[name][[config.prediction_contract.target_column]].rename(
            columns={config.prediction_contract.target_column: "target"}
        )
        identifiers = split_frames[name][
            ["admission_id", "patient_id", "admission_datetime"]
        ].copy()
        for kind, payload in (
            ("features", frame),
            ("target", target),
            ("identifiers", identifiers),
        ):
            write_dataset(payload, output_directory / f"{name}_{kind}", config.outputs.formats)
            output_checksums[f"{name}_{kind}"] = frame_fingerprint(payload)

    feature_registry = build_feature_registry(config, preprocessor)
    preprocessor_metadata = {
        **preprocessor.metadata,
        "training_split_fingerprint": frame_fingerprint(split_frames["train"]),
        "artefact_semantic_fingerprint": preprocessor.metadata["semantic_fingerprint"],
        "persisted_preprocessor_location": (
            "data/processed/features/preprocessor_metadata_only.json"
        ),
    }
    (output_directory / "preprocessor_metadata_only.json").write_text(
        json.dumps(preprocessor_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    counts = {
        "source_row_count": len(source.frame),
        "eligible_row_count": eligibility.summary["eligible_count"],
        "excluded_row_count": eligibility.summary["excluded_count"],
        "final_feature_count": len(preprocessor.output_columns),
    }
    manifest = manifest_payload(
        config=config,
        source_fingerprint=source.source_fingerprint,
        database_build_identifier=source.database_build_identifier,
        split_fingerprint=split.fingerprint,
        output_checksums=output_checksums,
        counts=counts,
    )
    write_json(evidence_directory / "feature_build_manifest.json", manifest)
    write_json(evidence_directory / "feature_registry.json", feature_registry)
    write_json(evidence_directory / "split_summary.json", split.summary)
    write_json(evidence_directory / "exclusion_summary.json", eligibility.summary)
    write_json(evidence_directory / "leakage_report.json", leakage.report)
    write_json(evidence_directory / "preprocessor_metadata.json", preprocessor_metadata)
    write_markdown_report(evidence_directory / "feature_build_report.md", manifest, split.summary)
    return FeatureBuildResult(
        manifest=manifest,
        split_summary=split.summary,
        feature_registry=feature_registry,
        leakage_report=leakage.report,
        exclusion_summary=eligibility.summary,
        preprocessor_metadata=preprocessor_metadata,
        output_directory=output_directory,
        evidence_directory=evidence_directory,
    )
