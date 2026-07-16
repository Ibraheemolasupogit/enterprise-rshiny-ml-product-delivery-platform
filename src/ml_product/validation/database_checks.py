"""DuckDB validation checks for Milestone 3."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

from ml_product.validation.data_contracts import CURATED_VIEWS


def _fetch_count(connection: duckdb.DuckDBPyConnection, sql: str) -> int:
    row = connection.execute(sql).fetchone()
    if row is None:
        raise ValueError(f"Count query returned no rows: {sql}")
    return int(row[0])


def validate_database(database_path: Path) -> dict[str, Any]:
    connection = duckdb.connect(str(database_path), read_only=True)
    try:
        errors: list[str] = []
        counts: dict[str, int] = {}
        for object_name in [
            "raw.patients",
            "raw.admissions",
            "raw.diagnoses",
            "raw.ward_capacity",
            "raw.workforce",
            "raw.outcomes",
            "quality.data_quality_issues",
            "quality.rejected_records",
            *CURATED_VIEWS,
        ]:
            try:
                counts[object_name] = _fetch_count(
                    connection, f"select count(*) from {object_name}"
                )
            except Exception as exc:
                errors.append(f"{object_name} validation failed: {exc}")
        unexpected = _fetch_count(
            connection,
            "select count(*) from quality.validation_results where validation_status = 'failed'",
        )
        if unexpected:
            errors.append(f"{unexpected} validation checks failed")
        return {"valid": not errors, "errors": errors, "counts": counts}
    finally:
        connection.close()
