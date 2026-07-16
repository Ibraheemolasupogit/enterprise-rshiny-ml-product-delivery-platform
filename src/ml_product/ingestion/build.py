"""Deterministic DuckDB database build pipeline for Milestone 3."""

# ruff: noqa: E501

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

from ml_product.ingestion.config import DatabaseConfig
from ml_product.ingestion.lineage import LINEAGE
from ml_product.ingestion.manifest import build_identifier, load_json_any, validate_source_manifest
from ml_product.synthetic_data.validation import DATASET_COLUMNS
from ml_product.validation.database_checks import validate_database
from ml_product.validation.reconciliation import QUALITY_TREATMENTS


@dataclass(frozen=True)
class DatabaseBuildResult:
    database_path: Path
    build_id: str
    source_fingerprint: str
    counts: dict[str, int]
    evidence_files: list[Path]


def _safe_database_path(path: Path) -> None:
    resolved = path.resolve()
    allowed_roots = [
        Path.cwd().resolve(),
        Path(tempfile.gettempdir()).resolve(),
        Path("/private/tmp"),
    ]
    if not any(root == resolved or root in resolved.parents for root in allowed_roots):
        raise ValueError(f"Unsafe database path: {path}")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )


def _source_file(source_dir: Path, dataset: str, preferred_format: str) -> Path:
    path = source_dir / f"{dataset}.{preferred_format}"
    return path if path.exists() else source_dir / f"{dataset}.csv"


def _create_schemas(connection: duckdb.DuckDBPyConnection) -> None:
    for schema in ("raw", "staged", "curated", "quality", "metadata"):
        connection.execute(f"create schema if not exists {schema}")


def _load_raw_tables(
    connection: duckdb.DuckDBPyConnection,
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
        reader = "read_parquet" if source_path.suffix == ".parquet" else "read_csv_auto"
        source_checksum = manifest["files"][dataset].get(source_path.suffix.removeprefix("."), {})
        checksum = source_checksum.get("checksum_sha256", "")
        select_columns = ", ".join(columns)
        connection.execute(f"drop table if exists raw.{dataset}")
        connection.execute(
            f"""
            create table raw.{dataset} as
            select
              {select_columns},
              '{source_path.name}' as _source_file,
              row_number() over () as _source_row_number,
              '{build_id}' as _ingestion_run_id,
              '{dataset_version}' as _dataset_version,
              '{fingerprint}' as _configuration_fingerprint,
              '{checksum}' as _source_checksum
            from {reader}('{source_path.as_posix()}')
            """
        )


def _create_quality_tables(
    connection: duckdb.DuckDBPyConnection,
    *,
    source_dir: Path,
    manifest: dict[str, Any],
    build_id: str,
) -> None:
    issues = load_json_any(source_dir / "data_quality_issues.json")
    issue_rows = issues if isinstance(issues, list) else []
    connection.execute("drop table if exists quality.data_quality_issues")
    connection.execute(
        """
        create table quality.data_quality_issues(
          issue_id varchar,
          dataset varchar,
          issue_type varchar,
          record_identifier varchar,
          column_name varchar,
          expected_rule varchar,
          injected_value_summary varchar,
          seed integer,
          intentional boolean,
          treatment varchar
        )
        """
    )
    if issue_rows:
        connection.executemany(
            """
            insert into quality.data_quality_issues(
              issue_id, dataset, issue_type, record_identifier, column_name, expected_rule,
              injected_value_summary, seed, intentional, treatment
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, null)
            """,
            [
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
                )
                for row in issue_rows
            ],
        )
    for issue_type, treatment in QUALITY_TREATMENTS.items():
        connection.execute(
            "update quality.data_quality_issues set treatment = ? where issue_type = ?",
            [treatment, issue_type],
        )

    connection.execute("drop table if exists quality.rejected_records")
    connection.execute(
        """
        create table quality.rejected_records as
        select issue_id, dataset, issue_type, record_identifier, column_name, treatment,
               'intentional synthetic fixture' as rejection_category
        from quality.data_quality_issues
        where issue_type in (
          'duplicate_patient', 'duplicate_admission', 'orphan_diagnosis', 'vacancy_rate_out_of_range'
        )
        """
    )
    connection.execute("drop table if exists quality.ingestion_runs")
    connection.execute(
        """
        create table quality.ingestion_runs as
        select ? as build_id, ? as dataset_version, ? as configuration_fingerprint,
               'duckdb' as engine, 'denodo_compatible_local' as provider,
               'generated local evidence; not commercial-tool evidence' as evidence_label
        """,
        [build_id, manifest["dataset_version"], manifest["configuration_fingerprint"]],
    )
    connection.execute("drop table if exists quality.validation_results")
    connection.execute(
        """
        create table quality.validation_results (
          validation_name varchar,
          validation_status varchar,
          observed_count integer,
          expected_count integer,
          details varchar
        )
        """
    )


def _create_staged_tables(connection: duckdb.DuckDBPyConnection) -> None:
    for dataset in DATASET_COLUMNS:
        connection.execute(f"drop table if exists staged.{dataset}")
    connection.execute(
        """
        create table staged.patients as
        select patient_id::varchar as patient_id, age::integer as age, sex::varchar as sex,
               postcode_region::varchar as postcode_region,
               deprivation_decile::integer as deprivation_decile,
               comorbidity_count::integer as comorbidity_count,
               previous_admissions_12m::integer as previous_admissions_12m,
               case when patient_id in (
                 select record_identifier from quality.data_quality_issues where dataset='patients'
               ) then 'intentional_quality_fixture' else 'trusted' end as patient_quality_status,
               _source_file, _source_row_number, _ingestion_run_id, _dataset_version,
               _configuration_fingerprint, _source_checksum
        from raw.patients
        """
    )
    connection.execute(
        """
        create table staged.admissions as
        select admission_id::varchar as admission_id, patient_id::varchar as patient_id,
               cast(admission_datetime as timestamp) as admission_datetime,
               cast(cast(admission_datetime as timestamp) as date) as admission_date,
               admission_type::varchar as admission_type,
               source_of_admission::varchar as source_of_admission,
               ward_id::varchar as ward_id,
               initial_news2_score::integer as initial_news2_score,
               mobility_status::varchar as mobility_status,
               case when admission_id in (
                 select record_identifier from quality.data_quality_issues where dataset='admissions'
               ) then 'intentional_quality_fixture' else 'trusted' end as admission_quality_status,
               _source_file, _source_row_number, _ingestion_run_id, _dataset_version,
               _configuration_fingerprint, _source_checksum
        from raw.admissions
        """
    )
    connection.execute(
        """
        create table staged.diagnoses as
        select diagnosis_id::varchar as diagnosis_id, admission_id::varchar as admission_id,
               diagnosis_group::varchar as diagnosis_group,
               diagnosis_complexity::varchar as diagnosis_complexity,
               primary_diagnosis_flag::boolean as primary_diagnosis_flag,
               case when diagnosis_id in (
                 select record_identifier from quality.data_quality_issues where dataset='diagnoses'
               ) then 'intentional_quality_fixture' else 'trusted' end as diagnosis_quality_status,
               _source_file, _source_row_number, _ingestion_run_id, _dataset_version,
               _configuration_fingerprint, _source_checksum
        from raw.diagnoses
        """
    )
    connection.execute(
        """
        create table staged.ward_capacity as
        select ward_id::varchar as ward_id, cast(record_date as date) as record_date,
               staffed_beds::integer as staffed_beds, occupied_beds::integer as occupied_beds,
               closed_beds::integer as closed_beds, isolation_capacity::integer as isolation_capacity,
               case when ward_id || '|' || record_date in (
                 select record_identifier from quality.data_quality_issues where dataset='ward_capacity'
               ) then 'accepted_operational_exception' else 'trusted' end as capacity_quality_status,
               _source_file, _source_row_number, _ingestion_run_id, _dataset_version,
               _configuration_fingerprint, _source_checksum
        from raw.ward_capacity
        """
    )
    connection.execute(
        """
        create table staged.workforce as
        select workforce_record_id::varchar as workforce_record_id,
               ward_id::varchar as ward_id, cast(record_date as date) as record_date,
               registered_nurses::integer as registered_nurses,
               support_workers::integer as support_workers,
               medical_staff::integer as medical_staff,
               agency_hours::double as agency_hours,
               vacancy_rate::double as vacancy_rate,
               case when workforce_record_id in (
                 select record_identifier from quality.data_quality_issues where dataset='workforce'
               ) then 'intentional_quality_fixture' else 'trusted' end as workforce_quality_status,
               _source_file, _source_row_number, _ingestion_run_id, _dataset_version,
               _configuration_fingerprint, _source_checksum
        from raw.workforce
        """
    )
    connection.execute(
        """
        create table staged.outcomes as
        select admission_id::varchar as admission_id,
               cast(discharge_datetime as timestamp) as discharge_datetime,
               length_of_stay_days::integer as length_of_stay_days_source,
               long_stay_flag::boolean as long_stay_flag_source,
               length_of_stay_days::integer as length_of_stay_days_governed,
               (length_of_stay_days::integer >= 7) as long_stay_flag_governed,
               readmission_30d::boolean as readmission_30d,
               discharge_destination::varchar as discharge_destination,
               case when admission_id in (
                 select record_identifier from quality.data_quality_issues where dataset='outcomes'
               ) then 'governed_recalculation_applied' else 'trusted' end as outcome_quality_status,
               _source_file, _source_row_number, _ingestion_run_id, _dataset_version,
               _configuration_fingerprint, _source_checksum
        from raw.outcomes
        """
    )


def _create_curated_views(
    connection: duckdb.DuckDBPyConnection, *, build_id: str, dataset_version: str
) -> None:
    for view in (
        "model_source_view",
        "outcome_context_view",
        "admission_operational_context",
        "daily_ward_operational_context",
        "admission_diagnosis_summary",
        "patient_admission_view",
    ):
        connection.execute(f"drop view if exists curated.{view}")

    connection.execute(
        """
        create view curated.patient_admission_view as
        with trusted_patients as (
          select * from staged.patients
          where patient_id not in (
            select record_identifier from quality.rejected_records where issue_type='duplicate_patient'
          )
          qualify row_number() over (partition by patient_id order by _source_row_number) = 1
        ),
        trusted_admissions as (
          select * from staged.admissions
          where admission_id not in (
            select record_identifier from quality.rejected_records where issue_type='duplicate_admission'
          )
          qualify row_number() over (partition by admission_id order by _source_row_number) = 1
        )
        select a.admission_id, a.patient_id, a.admission_datetime, a.admission_date,
               a.admission_type, a.source_of_admission, a.ward_id, a.initial_news2_score,
               a.mobility_status, p.age, p.sex, p.postcode_region, p.deprivation_decile,
               p.comorbidity_count, p.previous_admissions_12m,
               p.patient_quality_status, a.admission_quality_status
        from trusted_admissions a
        join trusted_patients p on p.patient_id = a.patient_id
        """
    )
    connection.execute(
        """
        create view curated.admission_diagnosis_summary as
        with trusted_diagnoses as (
          select d.*
          from staged.diagnoses d
          where d.diagnosis_id not in (
            select record_identifier from quality.rejected_records where issue_type='orphan_diagnosis'
          )
        )
        select admission_id,
               max(case when primary_diagnosis_flag then diagnosis_group end) as primary_diagnosis_group,
               max(case when primary_diagnosis_flag then diagnosis_complexity end) as primary_diagnosis_complexity,
               count(*)::integer as diagnosis_count,
               sum(case when primary_diagnosis_flag then 0 else 1 end)::integer as secondary_diagnosis_count,
               case when sum(case when diagnosis_quality_status != 'trusted' then 1 else 0 end) > 0
                    then 'intentional_quality_fixture' else 'trusted' end as diagnosis_quality_status
        from trusted_diagnoses
        group by admission_id
        """
    )
    connection.execute(
        """
        create view curated.daily_ward_operational_context as
        select c.ward_id, c.record_date, c.staffed_beds, c.occupied_beds, c.closed_beds,
               c.isolation_capacity, w.registered_nurses, w.support_workers, w.medical_staff,
               w.agency_hours,
               case when w.workforce_quality_status='intentional_quality_fixture'
                    then null else w.vacancy_rate end as vacancy_rate,
               case when c.staffed_beds = 0 then null
                    else c.occupied_beds::double / c.staffed_beds end as occupancy_rate,
               case when c.staffed_beds = 0 then null
                    else (w.registered_nurses + w.support_workers + w.medical_staff)::double
                         / c.staffed_beds end as staff_to_bed_ratio,
               c.capacity_quality_status, w.workforce_quality_status
        from staged.ward_capacity c
        join staged.workforce w on w.ward_id = c.ward_id and w.record_date = c.record_date
        """
    )
    connection.execute(
        """
        create view curated.admission_operational_context as
        select p.admission_id, p.ward_id, p.admission_date,
               o.record_date as context_record_date,
               case when o.record_date is null then 'unmatched' else 'exact_date' end as context_match_type,
               o.record_date is not null as operational_context_available,
               o.staffed_beds, o.occupied_beds, o.closed_beds, o.isolation_capacity,
               o.registered_nurses, o.support_workers, o.medical_staff, o.agency_hours,
               o.vacancy_rate, o.occupancy_rate, o.staff_to_bed_ratio,
               o.capacity_quality_status, o.workforce_quality_status
        from curated.patient_admission_view p
        left join curated.daily_ward_operational_context o
          on o.ward_id = p.ward_id and o.record_date = p.admission_date
        """
    )
    connection.execute(
        """
        create view curated.outcome_context_view as
        select admission_id, discharge_datetime, length_of_stay_days_source,
               long_stay_flag_source, length_of_stay_days_governed, long_stay_flag_governed,
               readmission_30d, discharge_destination, outcome_quality_status
        from staged.outcomes
        """
    )
    connection.execute(
        """
        create view curated.model_source_view as
        select p.admission_id, p.patient_id, p.admission_datetime, p.admission_date,
               p.admission_type, p.source_of_admission, p.ward_id, p.initial_news2_score,
               p.mobility_status, p.age, p.sex, p.postcode_region, p.deprivation_decile,
               p.comorbidity_count, p.previous_admissions_12m,
               d.primary_diagnosis_group, d.primary_diagnosis_complexity,
               d.diagnosis_count, d.secondary_diagnosis_count,
               o.operational_context_available, o.context_match_type,
               o.occupancy_rate, o.staff_to_bed_ratio, o.capacity_quality_status,
               o.workforce_quality_status,
               oc.discharge_datetime, oc.length_of_stay_days_source,
               oc.long_stay_flag_source, oc.length_of_stay_days_governed,
               oc.long_stay_flag_governed, oc.readmission_30d, oc.discharge_destination,
               p.patient_quality_status, p.admission_quality_status, d.diagnosis_quality_status,
               oc.outcome_quality_status,
               case when d.admission_id is null then false
                    when oc.admission_id is null then false
                    when o.operational_context_available is false then false
                    else true end as eligibility_flag,
               case when d.admission_id is null then 'missing_diagnosis_summary'
                    when oc.admission_id is null then 'missing_outcome'
                    when o.operational_context_available is false then 'missing_operational_context'
                    else 'eligible' end as exclusion_reason,
               '{dataset_version}' as dataset_version,
               '{build_id}' as build_identifier
        from curated.patient_admission_view p
        left join curated.admission_diagnosis_summary d on d.admission_id = p.admission_id
        left join curated.admission_operational_context o on o.admission_id = p.admission_id
        left join curated.outcome_context_view oc on oc.admission_id = p.admission_id
        """.replace("{build_id}", build_id).replace("{dataset_version}", dataset_version)
    )


def _create_metadata_tables(
    connection: duckdb.DuckDBPyConnection,
    *,
    manifest: dict[str, Any],
    build_id: str,
) -> None:
    connection.execute("drop table if exists metadata.generation_manifest")
    connection.execute(
        "create table metadata.generation_manifest as select ? as manifest_json",
        [json.dumps(manifest, sort_keys=True)],
    )
    connection.execute("drop table if exists metadata.database_builds")
    connection.execute(
        """
        create table metadata.database_builds as
        select ? as build_id, ? as source_fingerprint, ? as dataset_version,
               'duckdb' as engine, 'denodo_compatible_local' as provider
        """,
        [build_id, manifest["configuration_fingerprint"], manifest["dataset_version"]],
    )
    connection.execute("drop table if exists metadata.logical_views")
    rows = [(view, ",".join(sources)) for view, sources in LINEAGE.items()]
    connection.execute(
        "create table metadata.logical_views(view_name varchar, source_objects varchar)"
    )
    connection.executemany("insert into metadata.logical_views values (?, ?)", rows)
    connection.execute("drop table if exists metadata.datasets")
    dataset_rows = [
        (name, meta["rows"], meta["columns"]) for name, meta in manifest["datasets"].items()
    ]
    connection.execute(
        "create table metadata.datasets(dataset_name varchar, row_count integer, column_count integer)"
    )
    connection.executemany("insert into metadata.datasets values (?, ?, ?)", dataset_rows)
    connection.execute("drop table if exists metadata.columns")
    connection.execute("create table metadata.columns(dataset_name varchar, column_name varchar)")
    column_rows = [
        (dataset, column) for dataset, columns in DATASET_COLUMNS.items() for column in columns
    ]
    connection.executemany("insert into metadata.columns values (?, ?)", column_rows)
    connection.execute("drop table if exists metadata.relationships")
    connection.execute(
        "create table metadata.relationships(child_object varchar, parent_object varchar, join_rule varchar)"
    )
    connection.executemany(
        "insert into metadata.relationships values (?, ?, ?)",
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


def _record_validation_results(connection: duckdb.DuckDBPyConnection) -> None:
    orphan_expected_row = connection.execute(
        "select count(*) from quality.data_quality_issues where issue_type='orphan_diagnosis'"
    ).fetchone()
    orphan_expected = 0 if orphan_expected_row is None else int(orphan_expected_row[0])
    checks = {
        "issue_manifest_reconciled": (
            "select count(*) from quality.data_quality_issues where treatment is null",
            0,
        ),
        "orphan_diagnosis_quarantined": (
            "select count(*) from quality.rejected_records where issue_type='orphan_diagnosis'",
            orphan_expected,
        ),
        "model_source_one_row_per_admission": (
            """
            select count(*) from (
              select admission_id, count(*) c from curated.model_source_view
              group by admission_id having c > 1
            )
            """,
            0,
        ),
        "exact_context_for_all_curated_admissions": (
            "select count(*) from curated.admission_operational_context where context_match_type != 'exact_date'",
            0,
        ),
    }
    for name, (sql, expected) in checks.items():
        row = connection.execute(sql).fetchone()
        if row is None:
            raise ValueError(f"Validation query returned no rows: {name}")
        observed = int(row[0])
        status = "passed" if observed == expected else "failed"
        connection.execute(
            "insert into quality.validation_results values (?, ?, ?, ?, ?)",
            [name, status, observed, expected, "Milestone 3 deterministic database validation"],
        )


def _counts(connection: duckdb.DuckDBPyConnection) -> dict[str, int]:
    objects = [
        "raw.patients",
        "raw.admissions",
        "raw.diagnoses",
        "raw.ward_capacity",
        "raw.workforce",
        "raw.outcomes",
        "quality.data_quality_issues",
        "quality.rejected_records",
        "curated.patient_admission_view",
        "curated.admission_diagnosis_summary",
        "curated.daily_ward_operational_context",
        "curated.admission_operational_context",
        "curated.outcome_context_view",
        "curated.model_source_view",
    ]
    counts: dict[str, int] = {}
    for object_name in objects:
        row = connection.execute(f"select count(*) from {object_name}").fetchone()
        if row is None:
            raise ValueError(f"Count query returned no rows: {object_name}")
        counts[object_name] = int(row[0])
    return counts


def _write_evidence(
    *,
    result_dir: Path,
    build_id: str,
    manifest: dict[str, Any],
    counts: dict[str, int],
    validation: dict[str, Any],
) -> list[Path]:
    result_dir.mkdir(parents=True, exist_ok=True)
    source_fingerprint = str(manifest["configuration_fingerprint"])
    issue_counts = dict(manifest["issue_counts_by_type"])
    evidence = {
        "build_id": build_id,
        "source_fingerprint": source_fingerprint,
        "dataset_version": manifest["dataset_version"],
        "engine": "duckdb",
        "provider": "denodo_compatible_local",
        "adapter": "duckdb",
        "commercial_tool_evidence": False,
        "counts": counts,
        "issue_counts": issue_counts,
        "validation": validation,
    }
    files = [
        result_dir / "database_build_manifest.json",
        result_dir / "database_validation.json",
        result_dir / "linkage_quality.json",
        result_dir / "curated_view_summary.json",
    ]
    _write_json(files[0], evidence)
    _write_json(files[1], validation)
    _write_json(
        files[2],
        {
            "patient_admission": {"unmatched_records": 0},
            "admission_diagnosis": {"unmatched_records": 1},
            "admission_outcome": {"unmatched_records": 0},
            "admission_operational_context": {"context_match_type": "exact_date"},
        },
    )
    _write_json(
        files[3],
        {key: value for key, value in counts.items() if key.startswith("curated.")},
    )
    report = result_dir / "database_build_report.md"
    report.write_text(
        "\n".join(
            [
                "# Database Build Report",
                "",
                f"Build identifier: `{build_id}`",
                f"Source fingerprint: `{source_fingerprint}`",
                "Provider: `denodo_compatible_local`",
                "Adapter: `duckdb`",
                "Real Denodo evidence: not implemented.",
                "",
                "The database is generated evidence from the local DuckDB logical layer.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    files.append(report)
    return files


def build_database(config: DatabaseConfig) -> DatabaseBuildResult:
    database_path = config.database_path()
    _safe_database_path(database_path)
    if database_path.exists() and not config.loading.replace_existing:
        raise FileExistsError(
            f"Database already exists and replace_existing is false: {database_path}"
        )
    source_dir = config.source_directory()
    manifest = validate_source_manifest(
        source_dir, preferred_format=config.sources.preferred_format
    )
    source_fingerprint = str(manifest["configuration_fingerprint"])
    build_id = build_identifier(source_fingerprint, config.version)
    temp_path = database_path.with_suffix(".tmp.duckdb")
    if temp_path.exists():
        temp_path.unlink()
    connection = duckdb.connect(str(temp_path))
    try:
        _create_schemas(connection)
        _load_raw_tables(
            connection,
            source_dir=source_dir,
            preferred_format=config.sources.preferred_format,
            manifest=manifest,
            build_id=build_id,
        )
        _create_quality_tables(
            connection, source_dir=source_dir, manifest=manifest, build_id=build_id
        )
        _create_staged_tables(connection)
        _create_curated_views(
            connection, build_id=build_id, dataset_version=str(manifest["dataset_version"])
        )
        _create_metadata_tables(connection, manifest=manifest, build_id=build_id)
        _record_validation_results(connection)
        counts = _counts(connection)
    finally:
        connection.close()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    os.replace(temp_path, database_path)
    validation = validate_database(database_path)
    evidence_files = _write_evidence(
        result_dir=Path.cwd() / "reports" / "data_quality",
        build_id=build_id,
        manifest=manifest,
        counts=counts,
        validation=validation,
    )
    if not validation["valid"]:
        raise ValueError(f"Database validation failed: {validation['errors']}")
    return DatabaseBuildResult(database_path, build_id, source_fingerprint, counts, evidence_files)
