import os
from pathlib import Path

import pytest

from ml_product.ingestion.build import build_database
from ml_product.ingestion.config import DatabaseConfig
from ml_product.ingestion.postgresql import (
    check_postgresql_readiness,
    count_postgresql_objects,
    load_synthetic_data_to_postgresql,
    run_postgresql_migrations,
    validate_postgresql_database,
)

pytestmark = pytest.mark.skipif(
    not os.environ.get("POSTGRES_PASSWORD"),
    reason="PostgreSQL integration tests require POSTGRES_PASSWORD and a running local service.",
)


def _config() -> DatabaseConfig:
    return DatabaseConfig.from_file(Path("config/database.yaml"))


def test_postgresql_migrations_are_repeatable() -> None:
    config = _config()

    check_postgresql_readiness(config)
    first = run_postgresql_migrations(config)
    second = run_postgresql_migrations(config)

    assert [path.name for path in first] == [path.name for path in second]
    assert len(first) >= 5


def test_postgresql_loads_sources_and_preserves_quality_controls(tmp_path: Path) -> None:
    config = _config()
    duckdb_config = config.with_overrides(database_path=tmp_path / "baseline.duckdb", replace=True)
    duckdb_result = build_database(duckdb_config)

    postgres_result = load_synthetic_data_to_postgresql(config)
    validation = validate_postgresql_database(config)
    counts = count_postgresql_objects(config)

    assert validation["valid"], validation["errors"]
    assert postgres_result.source_fingerprint == duckdb_result.source_fingerprint
    for dataset in (
        "patients",
        "admissions",
        "diagnoses",
        "ward_capacity",
        "workforce",
        "outcomes",
    ):
        assert counts[f"raw.{dataset}"] == duckdb_result.counts[f"raw.{dataset}"]
    assert counts["quality.data_quality_issues"] == 9
    assert counts["quality.rejected_records"] == 4
    assert (
        counts["curated.patient_admission_view"]
        == duckdb_result.counts["curated.patient_admission_view"]
    )
    assert (
        counts["curated.admission_diagnosis_summary"]
        == duckdb_result.counts["curated.admission_diagnosis_summary"]
    )
    assert (
        counts["curated.daily_ward_operational_context"]
        == duckdb_result.counts["curated.daily_ward_operational_context"]
    )
    assert counts["curated.model_source_view"] == duckdb_result.counts["curated.model_source_view"]
    assert validation["eligible_population"] == 117
