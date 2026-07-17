"""PostgreSQL foundation for the governed local datastore."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pandas as pd
import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from ml_product.ingestion.config import DatabaseConfig
from ml_product.ingestion.lineage import LINEAGE
from ml_product.ingestion.manifest import build_identifier, load_json_any, validate_source_manifest
from ml_product.synthetic_data.validation import DATASET_COLUMNS
from ml_product.utils.paths import repository_root
from ml_product.validation.reconciliation import QUALITY_TREATMENTS

RAW_METADATA_COLUMNS = [
    "_source_file",
    "_source_row_number",
    "_ingestion_run_id",
    "_dataset_version",
    "_configuration_fingerprint",
    "_source_checksum",
]

CURATED_OBJECTS = [
    "curated.patient_admission_view",
    "curated.admission_diagnosis_summary",
    "curated.daily_ward_operational_context",
    "curated.admission_operational_context",
    "curated.outcome_context_view",
    "curated.model_source_view",
]

COUNT_OBJECTS = [
    "raw.patients",
    "raw.admissions",
    "raw.diagnoses",
    "raw.ward_capacity",
    "raw.workforce",
    "raw.outcomes",
    "quality.data_quality_issues",
    "quality.rejected_records",
    *CURATED_OBJECTS,
]


def _required_row(row: Any | None) -> dict[str, Any]:
    if row is None:
        raise ValueError("PostgreSQL query unexpectedly returned no rows")
    return cast(dict[str, Any], row)


@dataclass(frozen=True)
class PostgresSettings:
    host: str
    port: int
    dbname: str
    user: str
    password: str

    @classmethod
    def from_env(cls, config: DatabaseConfig) -> PostgresSettings:
        env = config.engine.postgresql
        password = os.environ.get(env.password_env, "")
        if not password:
            raise ValueError(f"{env.password_env} must be set for PostgreSQL connections")
        return cls(
            host=os.environ.get(env.host_env, "127.0.0.1"),
            port=int(os.environ.get(env.port_env, "5432")),
            dbname=os.environ.get(env.database_env, "ml_product"),
            user=os.environ.get(env.user_env, "ml_product"),
            password=password,
        )

    def connect(self) -> Connection[Any]:
        return psycopg.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            row_factory=dict_row,
        )


@dataclass(frozen=True)
class PostgresLoadResult:
    build_id: str
    source_fingerprint: str
    counts: dict[str, int]


def selected_database_backend(config: DatabaseConfig) -> str:
    backend = os.environ.get(config.engine.postgresql.backend_env, config.engine.type)
    if backend not in {"duckdb", "postgresql"}:
        raise ValueError("DATABASE_BACKEND must be duckdb or postgresql")
    return backend


def migration_directory() -> Path:
    return repository_root() / "database" / "postgresql" / "migrations"


def migration_files() -> list[Path]:
    return sorted(migration_directory().glob("*.sql"))


def check_postgresql_readiness(config: DatabaseConfig) -> None:
    settings = PostgresSettings.from_env(config)
    with settings.connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("select 1 as ready")
            row = cursor.fetchone()
    if row is None or row["ready"] != 1:
        raise ValueError("PostgreSQL readiness check did not return the expected sentinel")


def run_postgresql_migrations(config: DatabaseConfig) -> list[Path]:
    settings = PostgresSettings.from_env(config)
    files = migration_files()
    if not files:
        raise ValueError("No PostgreSQL migration files found")
    with settings.connect() as connection:
        with connection.cursor() as cursor:
            for path in files:
                cursor.execute(path.read_text(encoding="utf-8"))
        connection.commit()
    return files


def _source_file(source_dir: Path, dataset: str, preferred_format: str) -> Path:
    path = source_dir / f"{dataset}.{preferred_format}"
    return path if path.exists() else source_dir / f"{dataset}.csv"


def _read_source(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        frame = pd.read_parquet(path)
    else:
        frame = pd.read_csv(path)
    return frame.astype(object)


def _clean_value(value: Any) -> Any:
    return None if pd.isna(value) else value


def _insert_rows(
    connection: Connection[Any], table_name: str, columns: list[str], rows: list[tuple[Any, ...]]
) -> None:
    placeholders = ", ".join(["%s"] * len(columns))
    column_sql = ", ".join(columns)
    with connection.cursor() as cursor:
        cursor.executemany(
            f"insert into {table_name} ({column_sql}) values ({placeholders})",
            rows,
        )


def _load_raw_tables(
    connection: Connection[Any],
    *,
    source_dir: Path,
    preferred_format: str,
    manifest: dict[str, Any],
    build_id: str,
) -> None:
    fingerprint = str(manifest["configuration_fingerprint"])
    dataset_version = str(manifest["dataset_version"])
    for dataset, columns in DATASET_COLUMNS.items():
        source_path = _source_file(source_dir, dataset, preferred_format)
        checksum_payload = manifest["files"][dataset].get(source_path.suffix.removeprefix("."), {})
        checksum = checksum_payload.get("checksum_sha256", "")
        frame = _read_source(source_path)
        rows: list[tuple[Any, ...]] = []
        for row_number, row in enumerate(frame[columns].to_dict("records"), start=1):
            rows.append(
                tuple(_clean_value(row[column]) for column in columns)
                + (
                    source_path.name,
                    row_number,
                    build_id,
                    dataset_version,
                    fingerprint,
                    checksum,
                )
            )
        _insert_rows(connection, f"raw.{dataset}", [*columns, *RAW_METADATA_COLUMNS], rows)


def _load_quality_tables(
    connection: Connection[Any], *, source_dir: Path, manifest: dict[str, Any], build_id: str
) -> None:
    issues = load_json_any(source_dir / "data_quality_issues.json")
    issue_rows = issues if isinstance(issues, list) else []
    rows = [
        (
            row["issue_id"],
            row["dataset"],
            row["issue_type"],
            row["record_identifier"],
            row["column"],
            row["expected_rule"],
            row["injected_value_summary"],
            row["seed"],
            row["intentional"],
            QUALITY_TREATMENTS.get(row["issue_type"]),
        )
        for row in issue_rows
    ]
    if rows:
        _insert_rows(
            connection,
            "quality.data_quality_issues",
            [
                "issue_id",
                "dataset",
                "issue_type",
                "record_identifier",
                "column_name",
                "expected_rule",
                "injected_value_summary",
                "seed",
                "intentional",
                "treatment",
            ],
            rows,
        )
    with connection.cursor() as cursor:
        cursor.execute(
            """
            insert into quality.rejected_records
            select issue_id, dataset, issue_type, record_identifier, column_name, treatment,
                   'intentional synthetic fixture' as rejection_category
            from quality.data_quality_issues
            where issue_type in (
              'duplicate_patient', 'duplicate_admission', 'orphan_diagnosis',
              'vacancy_rate_out_of_range'
            )
            """
        )
        cursor.execute(
            """
            insert into quality.ingestion_runs
            values (%s, %s, %s, 'postgresql', 'denodo_compatible_local',
                    'generated local evidence; not commercial-tool evidence')
            """,
            (
                build_id,
                str(manifest["dataset_version"]),
                str(manifest["configuration_fingerprint"]),
            ),
        )


def _refresh_staged_tables(connection: Connection[Any]) -> None:
    statements = [
        """
        insert into staged.patients
        select patient_id, age, sex, postcode_region, deprivation_decile, comorbidity_count,
               previous_admissions_12m,
               case when patient_id in (
                 select record_identifier from quality.data_quality_issues
                 where dataset = 'patients'
               ) then 'intentional_quality_fixture' else 'trusted' end,
               _source_file, _source_row_number, _ingestion_run_id, _dataset_version,
               _configuration_fingerprint, _source_checksum
        from raw.patients
        """,
        """
        insert into staged.admissions
        select admission_id, patient_id, admission_datetime, admission_datetime::date,
               admission_type, source_of_admission, ward_id, initial_news2_score, mobility_status,
               case when admission_id in (
                 select record_identifier from quality.data_quality_issues
                 where dataset = 'admissions'
               ) then 'intentional_quality_fixture' else 'trusted' end,
               _source_file, _source_row_number, _ingestion_run_id, _dataset_version,
               _configuration_fingerprint, _source_checksum
        from raw.admissions
        """,
        """
        insert into staged.diagnoses
        select diagnosis_id, admission_id, diagnosis_group, diagnosis_complexity,
               primary_diagnosis_flag,
               case when diagnosis_id in (
                 select record_identifier from quality.data_quality_issues
                 where dataset = 'diagnoses'
               ) then 'intentional_quality_fixture' else 'trusted' end,
               _source_file, _source_row_number, _ingestion_run_id, _dataset_version,
               _configuration_fingerprint, _source_checksum
        from raw.diagnoses
        """,
        """
        insert into staged.ward_capacity
        select ward_id, record_date, staffed_beds, occupied_beds, closed_beds, isolation_capacity,
               case when ward_id || '|' || record_date::text in (
                 select record_identifier from quality.data_quality_issues
                 where dataset = 'ward_capacity'
               ) then 'accepted_operational_exception' else 'trusted' end,
               _source_file, _source_row_number, _ingestion_run_id, _dataset_version,
               _configuration_fingerprint, _source_checksum
        from raw.ward_capacity
        """,
        """
        insert into staged.workforce
        select workforce_record_id, ward_id, record_date, registered_nurses, support_workers,
               medical_staff, agency_hours, vacancy_rate,
               case when workforce_record_id in (
                 select record_identifier from quality.data_quality_issues
                 where dataset = 'workforce'
               ) then 'intentional_quality_fixture' else 'trusted' end,
               _source_file, _source_row_number, _ingestion_run_id, _dataset_version,
               _configuration_fingerprint, _source_checksum
        from raw.workforce
        """,
        """
        insert into staged.outcomes
        select admission_id, discharge_datetime, length_of_stay_days, long_stay_flag,
               length_of_stay_days, length_of_stay_days >= 7, readmission_30d,
               discharge_destination,
               case when admission_id in (
                 select record_identifier from quality.data_quality_issues
                 where dataset = 'outcomes'
               ) then 'governed_recalculation_applied' else 'trusted' end,
               _source_file, _source_row_number, _ingestion_run_id, _dataset_version,
               _configuration_fingerprint, _source_checksum
        from raw.outcomes
        """,
    ]
    with connection.cursor() as cursor:
        for dataset in DATASET_COLUMNS:
            cursor.execute(f"truncate table staged.{dataset}")
        for statement in statements:
            cursor.execute(statement)


def _load_metadata(connection: Connection[Any], *, manifest: dict[str, Any], build_id: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "insert into metadata.generation_manifest values (%s)",
            (json.dumps(manifest, sort_keys=True),),
        )
        cursor.execute(
            """
            insert into metadata.database_builds
            values (%s, %s, %s, 'postgresql', 'denodo_compatible_local')
            """,
            (
                build_id,
                str(manifest["configuration_fingerprint"]),
                str(manifest["dataset_version"]),
            ),
        )
        cursor.executemany(
            "insert into metadata.logical_views values (%s, %s)",
            [(view, ",".join(sources)) for view, sources in LINEAGE.items()],
        )
        cursor.executemany(
            "insert into metadata.datasets values (%s, %s, %s)",
            [(name, meta["rows"], meta["columns"]) for name, meta in manifest["datasets"].items()],
        )
        cursor.executemany(
            "insert into metadata.columns values (%s, %s)",
            [
                (dataset, column)
                for dataset, columns in DATASET_COLUMNS.items()
                for column in columns
            ],
        )
        cursor.executemany(
            "insert into metadata.relationships values (%s, %s, %s)",
            [
                ("admissions.patient_id", "patients.patient_id", "deterministic patient_id"),
                ("diagnoses.admission_id", "admissions.admission_id", "deterministic admission_id"),
                ("outcomes.admission_id", "admissions.admission_id", "deterministic admission_id"),
                (
                    "admissions.ward_id + admission_date",
                    "ward_capacity/workforce",
                    "exact same ward-date",
                ),
            ],
        )


def _record_validation_results(connection: Connection[Any]) -> None:
    checks = {
        "issue_manifest_reconciled": (
            "select count(*) from quality.data_quality_issues where treatment is null",
            0,
        ),
        "orphan_diagnosis_quarantined": (
            "select count(*) from quality.rejected_records where issue_type = 'orphan_diagnosis'",
            None,
        ),
        "model_source_one_row_per_admission": (
            """
            select count(*) from (
              select admission_id, count(*) c from curated.model_source_view
              group by admission_id having count(*) > 1
            ) duplicated
            """,
            0,
        ),
        "exact_context_for_all_curated_admissions": (
            """
            select count(*) from curated.admission_operational_context
            where context_match_type != 'exact_date'
            """,
            0,
        ),
    }
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select count(*) as observed
            from quality.data_quality_issues
            where issue_type = 'orphan_diagnosis'
            """
        )
        orphan_expected = int(_required_row(cursor.fetchone())["observed"])
        for name, (sql, expected_value) in checks.items():
            expected = orphan_expected if expected_value is None else expected_value
            cursor.execute(sql)
            observed = int(_required_row(cursor.fetchone())["count"])
            status = "passed" if observed == expected else "failed"
            cursor.execute(
                "insert into quality.validation_results values (%s, %s, %s, %s, %s)",
                (
                    name,
                    status,
                    observed,
                    expected,
                    "Milestone 14.1 PostgreSQL database validation",
                ),
            )


def _truncate_loaded_tables(connection: Connection[Any]) -> None:
    with connection.cursor() as cursor:
        for table in (
            "quality.validation_results",
            "quality.ingestion_runs",
            "quality.rejected_records",
            "quality.data_quality_issues",
            "metadata.relationships",
            "metadata.columns",
            "metadata.datasets",
            "metadata.logical_views",
            "metadata.database_builds",
            "metadata.generation_manifest",
        ):
            cursor.execute(f"truncate table {table}")
        for dataset in DATASET_COLUMNS:
            cursor.execute(f"truncate table raw.{dataset}")
            cursor.execute(f"truncate table staged.{dataset}")


def count_postgresql_objects(config: DatabaseConfig) -> dict[str, int]:
    settings = PostgresSettings.from_env(config)
    counts: dict[str, int] = {}
    with settings.connect() as connection:
        with connection.cursor() as cursor:
            for object_name in COUNT_OBJECTS:
                cursor.execute(f"select count(*) as count from {object_name}")
                counts[object_name] = int(_required_row(cursor.fetchone())["count"])
    return counts


def load_synthetic_data_to_postgresql(config: DatabaseConfig) -> PostgresLoadResult:
    run_postgresql_migrations(config)
    source_dir = config.source_directory()
    manifest = validate_source_manifest(
        source_dir, preferred_format=config.sources.preferred_format
    )
    source_fingerprint = str(manifest["configuration_fingerprint"])
    build_id = build_identifier(source_fingerprint, config.version)
    settings = PostgresSettings.from_env(config)
    with settings.connect() as connection:
        _truncate_loaded_tables(connection)
        _load_raw_tables(
            connection,
            source_dir=source_dir,
            preferred_format=config.sources.preferred_format,
            manifest=manifest,
            build_id=build_id,
        )
        _load_quality_tables(
            connection, source_dir=source_dir, manifest=manifest, build_id=build_id
        )
        _refresh_staged_tables(connection)
        _load_metadata(connection, manifest=manifest, build_id=build_id)
        _record_validation_results(connection)
        connection.commit()
    return PostgresLoadResult(build_id, source_fingerprint, count_postgresql_objects(config))


def validate_postgresql_database(config: DatabaseConfig) -> dict[str, Any]:
    run_postgresql_migrations(config)
    errors: list[str] = []
    expected_raw_columns = {
        dataset: [*columns, *RAW_METADATA_COLUMNS] for dataset, columns in DATASET_COLUMNS.items()
    }
    settings = PostgresSettings.from_env(config)
    counts: dict[str, int] = {}
    with settings.connect() as connection:
        with connection.cursor() as cursor:
            for dataset, expected_columns in expected_raw_columns.items():
                cursor.execute(
                    """
                    select column_name
                    from information_schema.columns
                    where table_schema = 'raw' and table_name = %s
                    order by ordinal_position
                    """,
                    (dataset,),
                )
                observed_columns = [row["column_name"] for row in cursor.fetchall()]
                if observed_columns != expected_columns:
                    errors.append(f"raw.{dataset} columns differ from source contract")
            for object_name in COUNT_OBJECTS:
                cursor.execute(f"select count(*) as count from {object_name}")
                counts[object_name] = int(_required_row(cursor.fetchone())["count"])
            cursor.execute(
                """
                select count(*) as count
                from quality.validation_results
                where validation_status != 'passed'
                """
            )
            failed_validations = int(_required_row(cursor.fetchone())["count"])
            if failed_validations:
                errors.append("PostgreSQL quality.validation_results contains failed checks")
            cursor.execute(
                "select count(*) as count from curated.model_source_view where eligibility_flag"
            )
            eligible_population = int(_required_row(cursor.fetchone())["count"])
    return {
        "valid": not errors,
        "errors": errors,
        "counts": counts,
        "eligible_population": eligible_population,
    }
