"""Verify deterministic Milestone 5 feature builds."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from ml_product.features.builder import build_features
from ml_product.features.config import FeatureConfig
from ml_product.features.metadata import stable_manifest
from ml_product.ingestion.build import build_database
from ml_product.ingestion.config import DatabaseConfig
from ml_product.utils.paths import repository_root

VOLATILE_KEYS = {"generated_at_utc"}


def main() -> int:
    root = repository_root()
    config = FeatureConfig.from_file(root / "config/features.yaml")
    database_config = DatabaseConfig.from_file(root / "config/database.yaml")
    with tempfile.TemporaryDirectory(prefix="feature-build-") as tmp:
        tmp_path = Path(tmp)
        database_path = tmp_path / "ml_product.duckdb"
        db_result = build_database(
            database_config.with_overrides(database_path=database_path, replace=True)
        )
        first_output = tmp_path / "features-a"
        second_output = tmp_path / "features-b"
        first = build_features(
            config,
            database_path=db_result.database_path,
            output_dir=first_output,
            evidence_dir=tmp_path / "evidence-a",
            replace=True,
        )
        second = build_features(
            config,
            database_path=db_result.database_path,
            output_dir=second_output,
            evidence_dir=tmp_path / "evidence-b",
            replace=True,
        )
        if stable_manifest(first.manifest) != stable_manifest(second.manifest):
            raise AssertionError("Stable feature manifests differ for identical source/config.")
        if first.split_summary != second.split_summary:
            raise AssertionError("Split summaries differ for identical source/config.")
        if first.feature_registry != second.feature_registry:
            raise AssertionError("Feature registries differ for identical source/config.")
        if first.preprocessor_metadata != second.preprocessor_metadata:
            raise AssertionError("Preprocessor metadata differs for identical source/config.")
        _compare_outputs(first_output, second_output)
        if first.split_summary["patient_overlap_count"] != 0:
            raise AssertionError("Patient overlap detected.")
        if first.leakage_report["total_violations"] != 0:
            raise AssertionError("Leakage violations detected.")
        changed = config.model_copy(
            deep=True,
            update={
                "splitting": config.splitting.model_copy(
                    update={"train_fraction": 0.5, "validation_fraction": 0.3, "test_fraction": 0.2}
                )
            },
        )
        changed_result = build_features(
            changed,
            database_path=db_result.database_path,
            output_dir=tmp_path / "features-c",
            evidence_dir=tmp_path / "evidence-c",
            replace=True,
        )
        if (
            changed_result.split_summary["split_fingerprint"]
            == first.split_summary["split_fingerprint"]
        ):
            raise AssertionError("Changed split configuration did not change split fingerprint.")
    print("Feature build reproducibility verified.")
    return 0


def _compare_outputs(left: Path, right: Path) -> None:
    for name in (
        "train_features",
        "validation_features",
        "test_features",
        "train_target",
        "validation_target",
        "test_target",
        "train_identifiers",
        "validation_identifiers",
        "test_identifiers",
    ):
        left_frame = pd.read_parquet(left / f"{name}.parquet")
        right_frame = pd.read_parquet(right / f"{name}.parquet")
        pd.testing.assert_frame_equal(left_frame, right_frame)
        left_csv = pd.read_csv(left / f"{name}.csv")
        right_csv = pd.read_csv(right / f"{name}.csv")
        pd.testing.assert_frame_equal(left_csv, right_csv)


if __name__ == "__main__":
    raise SystemExit(main())
