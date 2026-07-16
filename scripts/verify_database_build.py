"""Verify deterministic DuckDB database rebuild semantics."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from ml_product.ingestion.build import build_database
from ml_product.ingestion.config import DatabaseConfig

ROOT = Path(__file__).resolve().parents[1]


def stable_evidence(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "build_id": payload["build_id"],
        "source_fingerprint": payload["source_fingerprint"],
        "dataset_version": payload["dataset_version"],
        "engine": payload["engine"],
        "provider": payload["provider"],
        "counts": payload["counts"],
        "issue_counts": payload["issue_counts"],
    }


def main() -> int:
    config = DatabaseConfig.from_file(ROOT / "config" / "database.yaml")
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        first_config = config.with_overrides(
            database_path=Path(first) / "first.duckdb", replace=True
        )
        second_config = config.with_overrides(
            database_path=Path(second) / "second.duckdb", replace=True
        )
        first_result = build_database(first_config)
        first_evidence = stable_evidence(ROOT / "reports/data_quality/database_build_manifest.json")
        second_result = build_database(second_config)
        second_evidence = stable_evidence(
            ROOT / "reports/data_quality/database_build_manifest.json"
        )
        if first_result.build_id != second_result.build_id:
            raise AssertionError("Build identifiers differ for identical sources")
        if first_result.counts != second_result.counts:
            raise AssertionError("Object counts differ for identical sources")
        if first_evidence != second_evidence:
            raise AssertionError("Stable database build evidence differs")
    build_database(config.with_overrides(replace=True))
    print("Database build determinism verification passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Database build determinism verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
