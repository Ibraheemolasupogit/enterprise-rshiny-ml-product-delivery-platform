"""Milestone foundation and synthetic-data command-line interface."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Any, Literal, cast

import typer

from ml_product import __version__
from ml_product.features.builder import build_features
from ml_product.features.config import FeatureConfig
from ml_product.features.leakage import check_leakage
from ml_product.features.validation import validate_feature_outputs
from ml_product.ingestion.build import build_database
from ml_product.ingestion.client_factory import build_logical_view_client
from ml_product.ingestion.config import DatabaseConfig
from ml_product.ingestion.denodo_client import DenodoConnectionError
from ml_product.ingestion.postgresql import (
    check_postgresql_readiness,
    load_synthetic_data_to_postgresql,
    run_postgresql_migrations,
    validate_postgresql_database,
)
from ml_product.ingestion.postgresql_view_client import PostgreSQLViewClient
from ml_product.lifecycle import (
    LifecycleConfig,
    build_lifecycle_provider,
    build_model_package,
    run_lifecycle_workflow,
    validate_workflow_evidence,
    write_model_package,
)
from ml_product.lifecycle.identity import registration_fingerprint
from ml_product.lifecycle.linkage import LinkageStore
from ml_product.lifecycle.metadata import comparable_metadata, reconcile_metadata
from ml_product.lifecycle.models import PromotionRequest
from ml_product.lifecycle.orchestration import WorkflowMode
from ml_product.modelling.config import ModelTrainingConfig, ThresholdConfig
from ml_product.modelling.training import train_models
from ml_product.modelling.validation import validate_model_outputs
from ml_product.monitoring import (
    build_monitoring_baseline,
    generate_monitoring_fixture,
    run_monitoring,
    validate_monitoring_evidence,
)
from ml_product.monitoring.config import DriftThresholdConfig, MonitoringConfig
from ml_product.registry.config import GovernanceConfig, RegistryConfig
from ml_product.registry.metadata import sha256_file
from ml_product.registry.models import ApprovalDecisionValue
from ml_product.registry.registry import LocalModelRegistry
from ml_product.registry.storage import copy_immutable
from ml_product.release import (
    ReleaseConfig,
    assess_release_readiness,
    build_release_manifest,
    validate_release_config,
)
from ml_product.release.reporting import generate_release_assurance
from ml_product.release.validation import validate_containers
from ml_product.retraining import (
    ComparisonConfig,
    RetrainingConfig,
    assess_eligibility,
    prepare_dataset,
    register_retraining_candidate_fixture,
    run_retraining,
    validate_retraining_evidence,
)
from ml_product.serving.config import ServingConfig
from ml_product.serving.validation import validate_serving
from ml_product.settings import load_settings
from ml_product.synthetic_data.config import DatasetMode, SyntheticDataConfig
from ml_product.synthetic_data.generator import generate_synthetic_data
from ml_product.synthetic_data.validation import load_tables_from_directory, validate_tables
from ml_product.utils.paths import repository_root
from ml_product.validation.data_contracts import CURATED_VIEWS

app = typer.Typer(help="Milestone foundation utilities.")


def _run_compose(*args: str) -> None:
    result = subprocess.run(
        ["docker", "compose", *args],
        cwd=repository_root(),
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise typer.Exit(result.returncode)


def _run_postgresql_compose(*args: str) -> None:
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.postgresql.yml", *args],
        cwd=repository_root(),
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise typer.Exit(result.returncode)


def _run_validator(*args: str) -> None:
    script = repository_root() / "scripts" / "validate_repository.py"
    result = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=repository_root(),
        check=False,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        typer.echo(result.stdout.rstrip())
    if result.returncode != 0:
        if result.stderr:
            typer.echo(result.stderr.rstrip(), err=True)
        raise typer.Exit(result.returncode)


@app.command()
def version() -> None:
    """Print the package version."""

    typer.echo(__version__)


@app.command("validate-structure")
def validate_structure() -> None:
    """Validate required Milestone 1 repository structure."""

    _run_validator("--structure")


@app.command("validate-config")
def validate_config() -> None:
    """Validate Milestone 1 YAML configuration and environment modes."""

    load_settings()
    _run_validator("--config")


@app.command("generate-synthetic-data")
def generate_synthetic_data_command(
    config_path: Annotated[
        Path,
        typer.Option("--config", help="Synthetic-data YAML configuration path."),
    ] = Path("config/synthetic_data.yaml"),
    mode: Annotated[DatasetMode | None, typer.Option("--mode", help="Generation mode.")] = None,
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", help="Override output directory."),
    ] = None,
    seed: Annotated[int | None, typer.Option("--seed", help="Override deterministic seed.")] = None,
    clean: Annotated[
        bool, typer.Option("--clean", help="Disable intentional quality issues.")
    ] = False,
    overwrite: Annotated[
        bool, typer.Option("--overwrite", help="Allow overwriting output files.")
    ] = False,
) -> None:
    """Generate deterministic synthetic source-system datasets."""

    try:
        config = SyntheticDataConfig.from_file(config_path)
        config = config.with_overrides(
            mode=mode,
            output_dir=output_dir,
            seed=seed,
            clean=clean,
            overwrite=True if overwrite else None,
        )
        result = generate_synthetic_data(config)
    except Exception as exc:
        typer.echo(f"Generation failed: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(
        f"Generated synthetic data in {result.output_directory} "
        f"with {len(result.summary['datasets'])} datasets and {len(result.issues)} issues."
    )


@app.command("validate-synthetic-data")
def validate_synthetic_data_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/synthetic_data.yaml"),
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
) -> None:
    """Validate generated synthetic source-system datasets."""

    try:
        config = SyntheticDataConfig.from_file(config_path)
        directory = output_dir or config.output_directory()
        tables = load_tables_from_directory(directory)
        import json

        issues = json.loads((directory / "data_quality_issues.json").read_text(encoding="utf-8"))
        errors = validate_tables(tables, issues)
        if errors:
            raise ValueError("; ".join(errors))
    except Exception as exc:
        typer.echo(f"Synthetic data validation failed: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Synthetic data validation passed for {directory}.")


@app.command("describe-synthetic-data")
def describe_synthetic_data_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/synthetic_data.yaml"),
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
) -> None:
    """Print concise metadata about generated synthetic datasets."""

    try:
        import json

        config = SyntheticDataConfig.from_file(config_path)
        directory = output_dir or config.output_directory()
        manifest = json.loads((directory / "generation_manifest.json").read_text(encoding="utf-8"))
    except Exception as exc:
        typer.echo(f"Could not describe synthetic data: {exc}", err=True)
        raise typer.Exit(1) from exc

    typer.echo(f"Dataset version: {manifest['dataset_version']}")
    typer.echo(f"Seed: {manifest['seed']}")
    typer.echo(f"Configuration fingerprint: {manifest['configuration_fingerprint']}")
    typer.echo(f"Date range: {manifest['date_range']}")
    typer.echo(f"Total issues: {manifest['total_issue_count']}")
    for dataset, metadata in manifest["datasets"].items():
        typer.echo(f"- {dataset}: {metadata['rows']} rows, {metadata['columns']} columns")


@app.command("build-database")
def build_database_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
    source_dir: Annotated[Path | None, typer.Option("--source-dir")] = None,
    database_path: Annotated[Path | None, typer.Option("--database-path")] = None,
    replace: Annotated[bool, typer.Option("--replace")] = False,
    clean_source_only: Annotated[bool, typer.Option("--clean-source-only")] = False,
    source_format: Annotated[
        str | None, typer.Option("--source-format", help="Override source format: parquet or csv.")
    ] = None,
) -> None:
    """Build the local DuckDB source database and governed logical views."""

    try:
        if source_format not in {None, "parquet", "csv"}:
            raise ValueError("--source-format must be parquet or csv")
        preferred_format = cast(Literal["parquet", "csv"] | None, source_format)
        config = DatabaseConfig.from_file(config_path).with_overrides(
            source_dir=source_dir,
            database_path=database_path,
            replace=True if replace else None,
            preferred_format=preferred_format,
        )
        if clean_source_only:
            typer.echo("Clean-source-only build uses whatever clean source directory is supplied.")
        result = build_database(config)
    except Exception as exc:
        typer.echo(f"Database build failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Built database {result.database_path} with build_id={result.build_id} "
        f"and {len(result.counts)} counted objects."
    )


@app.command("validate-database")
def validate_database_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
    database_path: Annotated[Path | None, typer.Option("--database-path")] = None,
) -> None:
    """Validate the local DuckDB database."""

    from ml_product.validation.database_checks import validate_database

    config = DatabaseConfig.from_file(config_path)
    path = database_path or config.database_path()
    result = validate_database(path)
    if not result["valid"]:
        typer.echo(f"Database validation failed: {result['errors']}", err=True)
        raise typer.Exit(1)
    typer.echo(f"Database validation passed for {path}.")


@app.command("describe-database")
def describe_database_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
) -> None:
    """Print database build metadata and row counts."""

    import json

    config = DatabaseConfig.from_file(config_path)
    evidence_path = repository_root() / "reports/data_quality/database_build_manifest.json"
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    typer.echo(f"Engine: {payload['engine']}")
    typer.echo(f"Database path: {config.engine.database_path}")
    typer.echo(f"Build identifier: {payload['build_id']}")
    typer.echo(f"Source fingerprint: {payload['source_fingerprint']}")
    for name, count in payload["counts"].items():
        typer.echo(f"- {name}: {count}")


@app.command("postgres-start")
def postgres_start_command() -> None:
    """Start the local PostgreSQL Compose service."""

    _run_postgresql_compose("up", "-d", "postgres")


@app.command("postgres-stop")
def postgres_stop_command() -> None:
    """Stop the local PostgreSQL Compose service."""

    _run_postgresql_compose("stop", "postgres")


@app.command("postgres-check-readiness")
def postgres_check_readiness_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
) -> None:
    """Check the configured PostgreSQL datastore is reachable."""

    try:
        check_postgresql_readiness(DatabaseConfig.from_file(config_path))
    except Exception as exc:
        typer.echo(f"PostgreSQL readiness check failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo("PostgreSQL readiness check passed.")


@app.command("postgres-migrate")
def postgres_migrate_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
) -> None:
    """Run idempotent PostgreSQL migrations."""

    try:
        migrations = run_postgresql_migrations(DatabaseConfig.from_file(config_path))
    except Exception as exc:
        typer.echo(f"PostgreSQL migration failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Applied {len(migrations)} PostgreSQL migration files.")


@app.command("postgres-load-synthetic-data")
def postgres_load_synthetic_data_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
) -> None:
    """Load synthetic source datasets into PostgreSQL."""

    try:
        result = load_synthetic_data_to_postgresql(DatabaseConfig.from_file(config_path))
    except Exception as exc:
        typer.echo(f"PostgreSQL synthetic data load failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Loaded PostgreSQL synthetic data with build_id={result.build_id} "
        f"and {len(result.counts)} counted objects."
    )


@app.command("postgres-validate")
def postgres_validate_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
) -> None:
    """Validate PostgreSQL row counts, schemas, and quality controls."""

    try:
        result = validate_postgresql_database(DatabaseConfig.from_file(config_path))
    except Exception as exc:
        typer.echo(f"PostgreSQL validation failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    if not result["valid"]:
        typer.echo(f"PostgreSQL validation failed: {result['errors']}", err=True)
        raise typer.Exit(1)
    typer.echo(
        "PostgreSQL validation passed with "
        f"{result['eligible_population']} eligible model-source rows."
    )


def _client(config_path: Path) -> Any:
    config = DatabaseConfig.from_file(config_path)
    return build_logical_view_client(
        config,
        default_limit=config.logical_layer.default_limit,
        max_limit=config.logical_layer.max_limit,
    )


@app.command("list-logical-views")
def list_logical_views_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
) -> None:
    """List governed logical views."""

    for view_name in _client(config_path).list_views():
        typer.echo(view_name)


@app.command("describe-logical-view")
def describe_logical_view_command(
    view_name: str,
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
) -> None:
    """Describe one governed logical view."""

    description = _client(config_path).describe_view(view_name)
    typer.echo(f"View: {description['view_name']}")
    typer.echo("Columns: " + ", ".join(description["columns"]))
    typer.echo("Lineage: " + ", ".join(description["lineage"]))


@app.command("query-logical-view")
def query_logical_view_command(
    view_name: str,
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
    limit: Annotated[int | None, typer.Option("--limit")] = None,
) -> None:
    """Safely query a governed logical view with a bounded row limit."""

    import json

    rows = _client(config_path).query_view(view_name, limit=limit)
    typer.echo(json.dumps(rows, default=str, indent=2))


def _denodo_client(config_path: Path) -> Any:
    config = DatabaseConfig.from_file(config_path)
    from ml_product.ingestion.denodo_client import DenodoClient

    return DenodoClient.from_config(
        config,
        default_limit=config.logical_layer.default_limit,
        max_limit=config.logical_layer.max_limit,
    )


def _view_count(client: Any, view_name: str, *, limit: int) -> int:
    return len(client.query_view(view_name, limit=limit))


@app.command("denodo-check-readiness")
def denodo_check_readiness_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
) -> None:
    """Check live Denodo ODBC readiness."""

    client = _denodo_client(config_path)
    result = client.health_check()
    if not result["healthy"]:
        typer.echo(f"Denodo readiness check failed: {result.get('error', result)}", err=True)
        raise typer.Exit(1)
    typer.echo("Denodo readiness check passed.")


@app.command("denodo-list-views")
def denodo_list_views_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
) -> None:
    """List expected governed Denodo virtual views."""

    for view_name in _denodo_client(config_path).list_views():
        typer.echo(view_name)


@app.command("denodo-validate-row-counts")
def denodo_validate_row_counts_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
) -> None:
    """Validate live Denodo governed virtual-view row counts."""

    try:
        config = DatabaseConfig.from_file(config_path)
        client = _denodo_client(config_path)
        for view_name in CURATED_VIEWS:
            count = _view_count(client, view_name, limit=config.logical_layer.max_limit)
            typer.echo(f"{view_name}: {count}")
        eligible = sum(
            1
            for row in client.query_view(
                "curated.model_source_view", limit=config.logical_layer.max_limit
            )
            if row.get("eligibility_flag") is True
        )
    except DenodoConnectionError as exc:
        typer.echo(f"Denodo validation failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    if eligible != 117:
        typer.echo(f"Denodo eligible model-source rows mismatch: {eligible} != 117", err=True)
        raise typer.Exit(1)
    typer.echo("Denodo row-count validation passed with 117 eligible model-source rows.")


@app.command("denodo-compare-postgresql")
def denodo_compare_postgresql_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
) -> None:
    """Compare Denodo and direct PostgreSQL governed model-source populations."""

    try:
        config = DatabaseConfig.from_file(config_path)
        denodo = _denodo_client(config_path)
        postgresql = PostgreSQLViewClient(
            config,
            default_limit=config.logical_layer.max_limit,
            max_limit=config.logical_layer.max_limit,
        )
        denodo_rows = denodo.query_view(
            "curated.model_source_view", limit=config.logical_layer.max_limit
        )
        postgres_rows = postgresql.query_view(
            "curated.model_source_view", limit=config.logical_layer.max_limit
        )
    except Exception as exc:
        typer.echo(f"Denodo/PostgreSQL comparison failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    denodo_ids = {row["admission_id"] for row in denodo_rows if row.get("eligibility_flag") is True}
    postgres_ids = {
        row["admission_id"] for row in postgres_rows if row.get("eligibility_flag") is True
    }
    if denodo_ids != postgres_ids:
        typer.echo(
            "Denodo/PostgreSQL eligible model-source populations differ: "
            f"denodo={len(denodo_ids)} postgresql={len(postgres_ids)}",
            err=True,
        )
        raise typer.Exit(1)
    typer.echo(f"Denodo/PostgreSQL model-source populations match: {len(denodo_ids)} rows.")


@app.command("denodo-sample")
def denodo_sample_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
    view_name: Annotated[str, typer.Option("--view")] = "curated.model_source_view",
    limit: Annotated[int, typer.Option("--limit")] = 5,
) -> None:
    """Read a bounded sample from a governed Denodo virtual view."""

    import json

    try:
        rows = _denodo_client(config_path).query_view(view_name, limit=limit)
    except Exception as exc:
        typer.echo(f"Denodo sample read failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(json.dumps(rows, default=str, indent=2))


@app.command("show-lineage")
def show_lineage_command(
    view_name: str,
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/database.yaml"),
) -> None:
    """Show lineage for one governed logical view."""

    for source_object in _client(config_path).get_lineage(view_name):
        typer.echo(source_object)


@app.command("build-features")
def build_features_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/features.yaml"),
    database_config_path: Annotated[Path | None, typer.Option("--database-config")] = None,
    database_path: Annotated[Path | None, typer.Option("--database-path")] = None,
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    replace: Annotated[bool, typer.Option("--replace")] = False,
) -> None:
    """Build deterministic admission-time feature datasets."""

    try:
        config = FeatureConfig.from_file(config_path)
        result = build_features(
            config,
            database_config_path=database_config_path,
            database_path=database_path,
            output_dir=output_dir,
            replace=replace,
        )
    except Exception as exc:
        typer.echo(f"Feature build failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Built features in {result.output_directory} with "
        f"build_id={result.manifest['feature_build_identifier']} and "
        f"{result.manifest['counts']['final_feature_count']} output features."
    )


@app.command("validate-features")
def validate_features_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/features.yaml"),
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
) -> None:
    """Validate feature outputs, evidence, leakage, and split contracts."""

    config = FeatureConfig.from_file(config_path)
    result = validate_feature_outputs(config, output_dir=output_dir)
    if not result["valid"]:
        typer.echo(f"Feature validation failed: {result['errors']}", err=True)
        raise typer.Exit(1)
    typer.echo(
        f"Feature validation passed with {result['feature_column_count']} transformed columns."
    )


@app.command("describe-features")
def describe_features_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/features.yaml"),
) -> None:
    """Print concise metadata about the current feature build."""

    import json

    config = FeatureConfig.from_file(config_path)
    evidence = config.resolved_evidence_directory()
    manifest = json.loads((evidence / "feature_build_manifest.json").read_text(encoding="utf-8"))
    split_summary = json.loads((evidence / "split_summary.json").read_text(encoding="utf-8"))
    exclusion = json.loads((evidence / "exclusion_summary.json").read_text(encoding="utf-8"))
    typer.echo(f"Dataset version: {manifest['dataset_version']}")
    typer.echo(f"Build identifier: {manifest['feature_build_identifier']}")
    typer.echo(f"Source fingerprint: {manifest['source_fingerprint']}")
    typer.echo(f"Prediction point: {manifest['prediction_point']}")
    typer.echo(f"Target: {manifest['target_column']}")
    typer.echo(f"Feature count: {manifest['counts']['final_feature_count']}")
    typer.echo(f"Eligible rows: {exclusion['eligible_count']}")
    typer.echo(f"Excluded rows: {exclusion['excluded_count']}")
    for split, payload in split_summary["splits"].items():
        typer.echo(
            f"- {split}: {payload['row_count']} rows, positive_rate={payload['positive_rate']}"
        )


@app.command("list-features")
def list_features_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/features.yaml"),
) -> None:
    """Print feature registry entries."""

    import json

    config = FeatureConfig.from_file(config_path)
    registry = json.loads(
        (config.resolved_evidence_directory() / "feature_registry.json").read_text(encoding="utf-8")
    )
    for entry in registry["features"]:
        typer.echo(f"{entry['feature_name']}: {entry['source_column']} ({entry['transformation']})")


@app.command("show-split-summary")
def show_split_summary_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/features.yaml"),
) -> None:
    """Print split boundaries, counts, and overlap checks."""

    import json

    config = FeatureConfig.from_file(config_path)
    summary = json.loads(
        (config.resolved_evidence_directory() / "split_summary.json").read_text(encoding="utf-8")
    )
    typer.echo(f"Allocation strategy: {summary['allocation_strategy']}")
    typer.echo(f"Split fingerprint: {summary['split_fingerprint']}")
    for split, payload in summary["splits"].items():
        typer.echo(
            f"- {split}: {payload['row_count']} rows, "
            f"{payload['patient_count']} patients, "
            f"{payload['minimum_admission_date']} to {payload['maximum_admission_date']}"
        )
    typer.echo(f"Patient overlap count: {summary['patient_overlap_count']}")
    typer.echo(f"Admission overlap count: {summary['admission_overlap_count']}")


@app.command("check-feature-leakage")
def check_feature_leakage_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/features.yaml"),
) -> None:
    """Run Milestone 5 leakage checks without training a model."""

    config = FeatureConfig.from_file(config_path)
    result = check_leakage(config)
    if not result.valid:
        typer.echo(f"Feature leakage check failed: {result.violations}", err=True)
        raise typer.Exit(1)
    typer.echo(
        f"Feature leakage check passed for {result.report['checked_predictor_count']} predictors."
    )


@app.command("train-models")
def train_models_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_training.yaml"),
    threshold_config_path: Annotated[Path, typer.Option("--threshold-config")] = Path(
        "config/model_thresholds.yaml"
    ),
    feature_config_path: Annotated[Path | None, typer.Option("--feature-config")] = None,
    feature_dir: Annotated[Path | None, typer.Option("--feature-dir")] = None,
    candidate_dir: Annotated[Path | None, typer.Option("--candidate-dir")] = None,
    report_dir: Annotated[Path | None, typer.Option("--report-dir")] = None,
    replace: Annotated[bool, typer.Option("--replace")] = False,
) -> None:
    """Train deterministic Milestone 6 candidate models."""

    del feature_config_path
    try:
        config = ModelTrainingConfig.from_file(config_path)
        thresholds = ThresholdConfig.from_file(threshold_config_path)
        result = train_models(
            config,
            thresholds,
            feature_dir=feature_dir,
            candidate_dir=candidate_dir,
            report_dir=report_dir,
            replace=replace,
        )
    except Exception as exc:
        typer.echo(f"Model training failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    recommendation = result.candidate_recommendation
    typer.echo(
        f"Trained models with selected={recommendation['recommended_model']} "
        f"calibration={recommendation['recommended_calibration']} "
        f"threshold={recommendation['selected_threshold']}."
    )


@app.command("validate-models")
def validate_models_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_training.yaml"),
    threshold_config_path: Annotated[Path, typer.Option("--threshold-config")] = Path(
        "config/model_thresholds.yaml"
    ),
) -> None:
    """Validate Milestone 6 model artefacts and evidence."""

    del threshold_config_path
    config = ModelTrainingConfig.from_file(config_path)
    result = validate_model_outputs(config)
    if not result["valid"]:
        typer.echo(f"Model validation failed: {result['errors']}", err=True)
        raise typer.Exit(1)
    typer.echo("Model validation passed.")


def _load_model_report(config_path: Path, file_name: str) -> dict[str, Any]:
    import json

    config = ModelTrainingConfig.from_file(config_path)
    payload = json.loads((config.report_directory() / file_name).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{file_name} must contain a JSON object.")
    return payload


@app.command("compare-models")
def compare_models_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_training.yaml"),
) -> None:
    """Print validation model comparison rows."""

    payload = _load_model_report(config_path, "model_comparison.json")
    for row in payload["rows"]:
        typer.echo(
            f"{row['model_family']}: pr_auc={row['pr_auc']}, "
            f"brier={row['brier_score']}, recall={row['recall']}, "
            f"precision={row['precision']}"
        )


@app.command("describe-model-results")
def describe_model_results_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_training.yaml"),
) -> None:
    """Print selected model and locked test summary."""

    recommendation = _load_model_report(config_path, "candidate_recommendation.json")
    test_metrics = _load_model_report(config_path, "test_metrics.json")
    metrics = test_metrics["metrics"]
    typer.echo(f"Selected candidate: {recommendation['recommended_model']}")
    typer.echo(f"Selected calibration: {recommendation['recommended_calibration']}")
    typer.echo(f"Selected threshold: {recommendation['selected_threshold']}")
    typer.echo(f"Recommendation status: {recommendation['recommendation_status']}")
    typer.echo(
        f"Locked test PR-AUC={metrics['pr_auc']} Brier={metrics['brier_score']} "
        f"Recall={metrics['recall']} Precision={metrics['precision']}"
    )


@app.command("show-threshold-analysis")
def show_threshold_analysis_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_training.yaml"),
) -> None:
    """Print selected threshold evidence."""

    payload = _load_model_report(config_path, "threshold_analysis.json")
    typer.echo(f"Selected threshold: {payload['selected_threshold']}")
    typer.echo(f"Selection rule: {payload['selection_rule']}")
    for row in payload["thresholds"][:5]:
        typer.echo(
            f"{row['threshold']}: recall={row['recall']} precision={row['precision']} "
            f"cost={row['total_weighted_cost']}"
        )


@app.command("show-calibration-report")
def show_calibration_report_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_training.yaml"),
) -> None:
    """Print selected calibration evidence."""

    payload = _load_model_report(config_path, "calibration_report.json")
    typer.echo(f"Selected method: {payload['selected_method']}")
    typer.echo(f"Selection reason: {payload['selection_reason']}")
    typer.echo(f"Isotonic eligibility: {payload['method_eligibility']['isotonic']}")


@app.command("show-fairness-report")
def show_fairness_report_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_training.yaml"),
) -> None:
    """Print subgroup fairness evidence."""

    payload = _load_model_report(config_path, "fairness_report.json")
    for group_name, rows in payload["groups"].items():
        typer.echo(f"{group_name}:")
        for row in rows:
            typer.echo(f"- {row['group']}: n={row['row_count']} suppressed={row['suppressed']}")


@app.command("show-candidate-recommendation")
def show_candidate_recommendation_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_training.yaml"),
) -> None:
    """Print candidate recommendation evidence."""

    payload = _load_model_report(config_path, "candidate_recommendation.json")
    typer.echo(f"Recommended model: {payload['recommended_model']}")
    typer.echo(f"Recommendation status: {payload['recommendation_status']}")
    typer.echo(f"Test set used for selection: {payload['test_set_used_for_selection']}")


@app.command("verify-model-reproducibility")
def verify_model_reproducibility_command() -> None:
    """Run the model-build reproducibility script."""

    _run_script("verify_model_build.py")


def _registry(
    registry_config_path: Path,
    governance_config_path: Path = Path("config/model_governance.yaml"),
) -> LocalModelRegistry:
    return LocalModelRegistry(
        RegistryConfig.from_file(registry_config_path),
        GovernanceConfig.from_file(governance_config_path),
    )


def _materialise_registered_artefacts(version: Any, candidate_dir: Path) -> None:
    root = repository_root()
    artefacts = version.artefacts
    for source_name, target_text, expected_checksum in (
        ("xgboost.json", artefacts.model_path, artefacts.model_sha256),
        ("calibrator.joblib", artefacts.calibrator_path, artefacts.calibrator_sha256),
    ):
        target = root / target_text
        if target.is_file():
            if sha256_file(target) != expected_checksum:
                raise ValueError(f"Registered artefact checksum mismatch: {target_text}")
            continue
        checksum = copy_immutable(candidate_dir / source_name, target)
        if checksum != expected_checksum:
            target.unlink(missing_ok=True)
            raise ValueError(f"Candidate artefact checksum mismatch for {target_text}")


@app.command("register-model")
def register_model_command(
    registry_config_path: Annotated[Path, typer.Option("--registry-config")] = Path(
        "config/model_registry.yaml"
    ),
    model_config_path: Annotated[Path, typer.Option("--model-config")] = Path(
        "config/model_training.yaml"
    ),
    candidate_identifier: Annotated[str, typer.Option("--candidate-identifier")] = "",
    candidate_dir: Annotated[Path, typer.Option("--candidate-dir")] = Path("models/candidate"),
    replace: Annotated[bool, typer.Option("--replace")] = False,
) -> None:
    """Register the Milestone 6 candidate in the local immutable registry."""

    del replace
    try:
        registry = _registry(registry_config_path)
        try:
            version = registry.register_candidate(
                candidate_identifier=candidate_identifier,
                model_config_path=model_config_path,
                candidate_dir=candidate_dir,
            )
        except ValueError as exc:
            if "already registered" not in str(exc):
                raise
            record = registry.load()
            version = next(
                item
                for entry in record.models
                for item in entry.versions
                if item.candidate_identifier == candidate_identifier
            )
            _materialise_registered_artefacts(version, candidate_dir)
            registry.write_evidence(record, version)
    except Exception as exc:
        typer.echo(f"Model registration failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Registered {version.model_name}:{version.registry_version} "
        f"status={version.status} candidate={version.candidate_identifier}."
    )


@app.command("validate-registry")
def validate_registry_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_registry.yaml"),
) -> None:
    """Validate local registry metadata and Milestone 7 evidence."""

    result = _registry(config_path).validate()
    if not result["valid"]:
        typer.echo(f"Registry validation failed: {result['errors']}", err=True)
        raise typer.Exit(1)
    typer.echo("Registry validation passed.")


@app.command("list-models")
def list_models_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_registry.yaml"),
) -> None:
    """List local registry model versions."""

    versions = _registry(config_path).list_models()
    for version in versions:
        typer.echo(
            f"{version.model_name}:{version.registry_version} "
            f"{version.model_family} {version.status} {version.candidate_identifier}"
        )


@app.command("show-model-version")
def show_model_version_command(
    model_name: Annotated[str, typer.Option("--model-name")],
    version: Annotated[int, typer.Option("--version")],
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_registry.yaml"),
) -> None:
    """Show one registry version."""

    item = _registry(config_path).get_model_version(model_name, version)
    typer.echo(item.model_dump_json(indent=2))


@app.command("submit-model-for-approval")
def submit_model_for_approval_command(
    model_name: Annotated[str, typer.Option("--model-name")] = "long_stay_admission_risk",
    version: Annotated[int, typer.Option("--version")] = 1,
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_registry.yaml"),
) -> None:
    """Move a registered model to approval-pending state."""

    try:
        item = _registry(config_path).submit_for_approval(model_name, version)
    except Exception as exc:
        typer.echo(f"Approval submission failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"{item.model_name}:{item.registry_version} status={item.status}")


@app.command("record-approval-decision")
def record_approval_decision_command(
    model_name: Annotated[str, typer.Option("--model-name")],
    version: Annotated[int, typer.Option("--version")],
    decision: Annotated[ApprovalDecisionValue, typer.Option("--decision")],
    actor: Annotated[str, typer.Option("--actor")],
    reason: Annotated[str, typer.Option("--reason")],
    conditions: Annotated[list[str] | None, typer.Option("--conditions")] = None,
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_registry.yaml"),
) -> None:
    """Record an explicit approval decision."""

    try:
        item = _registry(config_path).record_approval_decision(
            model_name=model_name,
            version=version,
            decision=decision,
            actor=actor,
            reason=reason,
            conditions=conditions or [],
        )
    except Exception as exc:
        typer.echo(f"Approval decision failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"{item.model_name}:{item.registry_version} status={item.status}")


@app.command("activate-model")
def activate_model_command(
    model_name: Annotated[str, typer.Option("--model-name")],
    version: Annotated[int, typer.Option("--version")],
    actor: Annotated[str, typer.Option("--actor")] = "LOCAL-GOVERNANCE-REVIEWER",
    reason: Annotated[str, typer.Option("--reason")] = "Explicit local activation command.",
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_registry.yaml"),
) -> None:
    """Activate an approved local model version."""

    try:
        item = _registry(config_path).activate_model(
            model_name=model_name,
            version=version,
            actor=actor,
            reason=reason,
        )
    except Exception as exc:
        typer.echo(f"Activation failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"{item.model_name}:{item.registry_version} status={item.status}")


@app.command("retire-model")
def retire_model_command(
    model_name: Annotated[str, typer.Option("--model-name")],
    version: Annotated[int, typer.Option("--version")],
    actor: Annotated[str, typer.Option("--actor")] = "LOCAL-GOVERNANCE-REVIEWER",
    reason: Annotated[str, typer.Option("--reason")] = "Explicit local retirement command.",
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_registry.yaml"),
) -> None:
    """Retire a model version."""

    try:
        item = _registry(config_path).retire_model(
            model_name=model_name, version=version, actor=actor, reason=reason
        )
    except Exception as exc:
        typer.echo(f"Retirement failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"{item.model_name}:{item.registry_version} status={item.status}")


@app.command("rollback-model")
def rollback_model_command(
    model_name: Annotated[str, typer.Option("--model-name")] = "long_stay_admission_risk",
    target_version: Annotated[int, typer.Option("--target-version")] = 1,
    reason: Annotated[str, typer.Option("--reason")] = "Local rollback validation.",
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    actor: Annotated[str, typer.Option("--actor")] = "LOCAL-GOVERNANCE-REVIEWER",
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_registry.yaml"),
) -> None:
    """Rollback to a previously approved-compatible model version."""

    try:
        item = _registry(config_path).rollback_model(
            model_name=model_name,
            target_version=target_version,
            actor=actor,
            reason=reason,
            dry_run=dry_run,
        )
    except Exception as exc:
        typer.echo(f"Rollback failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    status_text = "validated" if dry_run else "completed"
    typer.echo(f"Rollback {status_text} for {item.model_name}:{item.registry_version}")


@app.command("show-governance-review")
def show_governance_review_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_registry.yaml"),
) -> None:
    """Print generated governance review summary."""

    del config_path
    payload = _load_model_report(Path("config/model_training.yaml"), "governance_review.json")
    typer.echo(f"Recommended decision: {payload['recommended_decision']}")
    typer.echo(f"Human decision required: {payload['human_decision_required']}")
    for flag in payload["review_flags"]:
        typer.echo(f"- {flag['code']}: {flag['detail']}")


@app.command("lifecycle-check-readiness")
def lifecycle_check_readiness_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
) -> None:
    """Check the configured model-lifecycle provider readiness."""

    try:
        config = LifecycleConfig.from_file(config_path)
        provider = build_lifecycle_provider(config)
        result = provider.readiness_check()
    except Exception as exc:
        typer.echo(f"Lifecycle readiness failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Lifecycle provider={result['provider']} "
        f"label={result.get('provider_label')} healthy={result['healthy']}"
    )


@app.command("lifecycle-describe-provider")
def lifecycle_describe_provider_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
) -> None:
    """Describe the configured model-lifecycle provider boundary."""

    try:
        config = LifecycleConfig.from_file(config_path)
        provider = build_lifecycle_provider(config)
    except Exception as exc:
        typer.echo(f"Lifecycle provider configuration failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Selected provider: {provider.provider_name}")
    typer.echo(f"Local label: {config.local.provider_label}")
    typer.echo(f"SAS Viya label: {config.sas_viya.provider_label}")
    typer.echo(f"SAS Viya enabled: {config.sas_viya.enabled}")
    typer.echo(f"Model package output: {config.model_package.output_path}")


@app.command("lifecycle-build-model-package")
def lifecycle_build_model_package_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
    output_path: Annotated[Path | None, typer.Option("--output-path")] = None,
) -> None:
    """Build a portable model-lifecycle package from existing review evidence."""

    try:
        config = LifecycleConfig.from_file(config_path)
        package = build_model_package(config)
        destination = write_model_package(
            package,
            output_path or config.model_package.output_path,
        )
    except Exception as exc:
        typer.echo(f"Lifecycle package build failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    try:
        display_path = destination.relative_to(repository_root())
    except ValueError:
        display_path = destination
    typer.echo(
        f"Built lifecycle package for {package.model_name}:{package.model_version} "
        f"at {display_path}."
    )


@app.command("lifecycle-register-model")
def lifecycle_register_model_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Register or dry-run-register the lifecycle package with the selected provider."""

    try:
        config = LifecycleConfig.from_file(config_path)
        package = build_model_package(config)
        provider = build_lifecycle_provider(config)
        result = provider.register_model_package(package, dry_run=dry_run)
    except Exception as exc:
        typer.echo(f"Lifecycle registration failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(result.model_dump_json(indent=2))


@app.command("lifecycle-show-registration")
def lifecycle_show_registration_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
) -> None:
    """Show local linkage state for the configured lifecycle package."""

    try:
        config = LifecycleConfig.from_file(config_path)
        package = build_model_package(config)
        fingerprint = registration_fingerprint(package)
        provider = build_lifecycle_provider(config)
        record = LinkageStore(config.registration.linkage_path).find(
            provider.provider_name,
            fingerprint,
        )
    except Exception as exc:
        typer.echo(f"Lifecycle registration lookup failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    payload = {
        "provider": provider.provider_name,
        "registration_fingerprint": fingerprint,
        "found": record is not None,
        "record": None if record is None else record.model_dump(mode="json"),
    }
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@app.command("lifecycle-reconcile-registration")
def lifecycle_reconcile_registration_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
) -> None:
    """Reconcile configured local package metadata with linkage-compatible metadata."""

    try:
        config = LifecycleConfig.from_file(config_path)
        package = build_model_package(config)
        result = reconcile_metadata(
            package,
            {"customProperties": comparable_metadata(package)},
        )
    except Exception as exc:
        typer.echo(f"Lifecycle reconciliation failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(result.model_dump_json(indent=2))


@app.command("lifecycle-show-champion")
def lifecycle_show_champion_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
) -> None:
    """Show the current provider champion without changing local activation state."""

    try:
        config = LifecycleConfig.from_file(config_path)
        package = build_model_package(config)
        champion = build_lifecycle_provider(config).retrieve_current_champion(package.model_name)
    except Exception as exc:
        typer.echo(f"Lifecycle champion lookup failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    payload = {
        "found": champion is not None,
        "champion": None if champion is None else champion.model_dump(mode="json"),
    }
    typer.echo(json.dumps(payload, indent=2, sort_keys=True))


@app.command("lifecycle-list-challengers")
def lifecycle_list_challengers_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
) -> None:
    """List registered lifecycle challengers."""

    try:
        config = LifecycleConfig.from_file(config_path)
        package = build_model_package(config)
        challengers = build_lifecycle_provider(config).retrieve_registered_challengers(package)
    except Exception as exc:
        typer.echo(f"Lifecycle challenger listing failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        json.dumps(
            {"challengers": [item.model_dump(mode="json") for item in challengers]},
            indent=2,
            sort_keys=True,
        )
    )


@app.command("lifecycle-compare-champion")
def lifecycle_compare_champion_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
) -> None:
    """Compare current champion and configured challenger lifecycle metadata."""

    try:
        config = LifecycleConfig.from_file(config_path)
        package = build_model_package(config)
        result = build_lifecycle_provider(config).compare_champion_and_challenger(package)
    except Exception as exc:
        typer.echo(f"Lifecycle champion comparison failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(result.model_dump_json(indent=2))


@app.command("lifecycle-assess-promotion")
def lifecycle_assess_promotion_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Assess promotion eligibility without local activation."""

    try:
        config = LifecycleConfig.from_file(config_path)
        package = build_model_package(config)
        result = build_lifecycle_provider(config).submit_promotion_request(
            package,
            dry_run=dry_run,
        )
    except Exception as exc:
        typer.echo(f"Lifecycle promotion assessment failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(result.model_dump_json(indent=2))


@app.command("lifecycle-submit-promotion")
def lifecycle_submit_promotion_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
    confirm_external_promotion: Annotated[
        bool,
        typer.Option("--confirm-external-promotion"),
    ] = False,
) -> None:
    """Submit external provider promotion without activating the local model."""

    try:
        config = LifecycleConfig.from_file(config_path)
        package = build_model_package(config)
        provider = build_lifecycle_provider(config)
        comparison = provider.compare_champion_and_challenger(package)
        request = PromotionRequest(
            provider=provider.provider_name,
            model_name=package.model_name,
            local_model_id=package.registry_id,
            local_model_version=package.model_version,
            external_model_id=comparison.challenger.external_model_id,
            external_model_version_id=comparison.challenger.external_model_version_id,
            registration_fingerprint=comparison.challenger.registration_fingerprint,
            requested_by="CLI",
            reason="Explicit external lifecycle promotion command.",
        )
        result = provider.promote_approved_model_version(
            request,
            confirm_external=confirm_external_promotion,
        )
    except Exception as exc:
        typer.echo(f"Lifecycle promotion failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(result.model_dump_json(indent=2))


@app.command("lifecycle-show-promotion")
def lifecycle_show_promotion_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
) -> None:
    """Show current promotion eligibility state."""

    try:
        config = LifecycleConfig.from_file(config_path)
        package = build_model_package(config)
        result = build_lifecycle_provider(config).retrieve_promotion_state(package)
    except Exception as exc:
        typer.echo(f"Lifecycle promotion state failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(result.model_dump_json(indent=2))


@app.command("lifecycle-reconcile-promotion")
def lifecycle_reconcile_promotion_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
) -> None:
    """Reconcile external promotion/champion state with local activation state."""

    try:
        config = LifecycleConfig.from_file(config_path)
        package = build_model_package(config)
        result = build_lifecycle_provider(config).reconcile_lifecycle_state(package)
    except Exception as exc:
        typer.echo(f"Lifecycle promotion reconciliation failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(result.model_dump_json(indent=2))


@app.command("lifecycle-run-end-to-end")
def lifecycle_run_end_to_end_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
    mode: Annotated[WorkflowMode, typer.Option("--mode")] = "local_safe",
    json_output: Annotated[bool, typer.Option("--json")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    allow_external_registration: Annotated[
        bool,
        typer.Option("--allow-external-registration"),
    ] = False,
    allow_external_promotion: Annotated[
        bool,
        typer.Option("--allow-external-promotion"),
    ] = False,
    allow_local_activation: Annotated[bool, typer.Option("--allow-local-activation")] = False,
    stage: Annotated[list[str] | None, typer.Option("--stage")] = None,
) -> None:
    """Run canonical lifecycle orchestration without implicit mutations."""

    try:
        config = LifecycleConfig.from_file(config_path)
        provider = build_lifecycle_provider(config)
        run = run_lifecycle_workflow(
            config,
            provider,
            mode=mode,
            allow_external_registration=False if dry_run else allow_external_registration,
            allow_external_promotion=False if dry_run else allow_external_promotion,
            allow_local_activation=False if dry_run else allow_local_activation,
            selected_stages=set(stage) if stage else None,
        )
    except Exception as exc:
        typer.echo(f"Lifecycle workflow failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    if json_output:
        typer.echo(run.model_dump_json(indent=2))
        return
    assert run.summary is not None
    typer.echo(
        f"Workflow {run.workflow_id} {run.summary.status}: "
        f"passed={run.summary.passed_stages} blocked={run.summary.blocked_stages} "
        f"failed={run.summary.failed_stages} skipped={run.summary.skipped_stages}"
    )


@app.command("lifecycle-show-workflow")
def lifecycle_show_workflow_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Show the latest persisted lifecycle workflow state."""

    try:
        config = LifecycleConfig.from_file(config_path)
        payload = json.loads(
            (repository_root() / config.workflow.state_path).read_text(encoding="utf-8")
        )
    except Exception as exc:
        typer.echo(f"Lifecycle workflow lookup failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    if json_output:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
        return
    summary = payload.get("summary", {})
    typer.echo(
        f"Workflow {payload.get('workflow_id')} {summary.get('status')} "
        f"evidence={payload.get('evidence_bundle_path')}"
    )


@app.command("lifecycle-resume-workflow")
def lifecycle_resume_workflow_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
    mode: Annotated[WorkflowMode, typer.Option("--mode")] = "local_safe",
    restart_stage: Annotated[str | None, typer.Option("--restart-stage")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Resume a lifecycle workflow when fingerprints still match."""

    try:
        config = LifecycleConfig.from_file(config_path)
        provider = build_lifecycle_provider(config)
        run = run_lifecycle_workflow(
            config,
            provider,
            mode=mode,
            resume=True,
            restart_stage=restart_stage,
        )
    except Exception as exc:
        typer.echo(f"Lifecycle workflow resume failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    if json_output:
        typer.echo(run.model_dump_json(indent=2))
        return
    assert run.summary is not None
    typer.echo(f"Workflow {run.workflow_id} resumed with status={run.summary.status}")


@app.command("lifecycle-validate-workflow-evidence")
def lifecycle_validate_workflow_evidence_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/model_lifecycle.yaml"),
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Validate the latest lifecycle workflow evidence bundle checksum."""

    try:
        result = validate_workflow_evidence(LifecycleConfig.from_file(config_path))
    except Exception as exc:
        typer.echo(f"Lifecycle workflow evidence validation failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    if json_output:
        typer.echo(json.dumps(result, indent=2, sort_keys=True))
    else:
        typer.echo("Workflow evidence valid." if result["valid"] else "Workflow evidence invalid.")
    if not result["valid"]:
        raise typer.Exit(1)


@app.command("validate-serving")
def validate_serving_command(
    registry_config_path: Annotated[Path, typer.Option("--registry-config")] = Path(
        "config/model_registry.yaml"
    ),
    serving_config_path: Annotated[Path, typer.Option("--serving-config")] = Path(
        "config/serving.yaml"
    ),
) -> None:
    """Validate local serving readiness and closed-by-default behavior."""

    result = validate_serving(
        registry_config=RegistryConfig.from_file(registry_config_path),
        governance_config=GovernanceConfig.from_file(Path("config/model_governance.yaml")),
        serving_config=ServingConfig.from_file(serving_config_path),
    )
    if not result["valid"]:
        typer.echo(f"Serving validation failed: {result['errors']}", err=True)
        raise typer.Exit(1)
    typer.echo(
        f"Serving validation passed. approved_serving_ready={result['approved_serving_ready']} "
        f"default_ready={result['default_ready']}"
    )


@app.command("serve-model-api")
def serve_model_api_command(
    serving_config_path: Annotated[Path, typer.Option("--serving-config")] = Path(
        "config/serving.yaml"
    ),
) -> None:
    """Run the local FastAPI scoring API with Uvicorn."""

    import uvicorn

    config = ServingConfig.from_file(serving_config_path)
    uvicorn.run(
        "ml_product.serving.app:app_from_config",
        host=config.service.host,
        port=config.service.port,
        factory=True,
    )


def _run_script(script_name: str) -> None:
    script = repository_root() / "scripts" / script_name
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=repository_root(),
        check=False,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        typer.echo(result.stdout.rstrip())
    if result.returncode != 0:
        if result.stderr:
            typer.echo(result.stderr.rstrip(), err=True)
        raise typer.Exit(result.returncode)


@app.command("build-monitoring-baseline")
def build_monitoring_baseline_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/monitoring.yaml"),
    threshold_config_path: Annotated[Path, typer.Option("--threshold-config")] = Path(
        "config/drift_thresholds.yaml"
    ),
    replace: Annotated[bool, typer.Option("--replace")] = False,
) -> None:
    """Build deterministic local monitoring baseline evidence."""

    try:
        baseline = build_monitoring_baseline(
            MonitoringConfig.from_file(config_path),
            DriftThresholdConfig.from_file(threshold_config_path),
            replace=replace,
        )
    except Exception as exc:
        typer.echo(f"Monitoring baseline build failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Built monitoring baseline {baseline['baseline_identifier']} "
        f"for candidate {baseline['candidate_identifier']}."
    )


@app.command("generate-monitoring-fixture")
def generate_monitoring_fixture_command(
    scenario: Annotated[str, typer.Option("--scenario")] = "moderate_drift",
    output_dir: Annotated[Path, typer.Option("--output-dir")] = Path("tests/fixtures/monitoring"),
    replace: Annotated[bool, typer.Option("--replace")] = False,
) -> None:
    """Generate deterministic small synthetic monitoring fixture."""

    try:
        path = generate_monitoring_fixture(scenario, output_dir, replace=replace)
    except Exception as exc:
        typer.echo(f"Monitoring fixture generation failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Generated monitoring fixture: {path.relative_to(repository_root())}.")


@app.command("run-monitoring")
def run_monitoring_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/monitoring.yaml"),
    threshold_config_path: Annotated[Path, typer.Option("--threshold-config")] = Path(
        "config/drift_thresholds.yaml"
    ),
    current_window: Annotated[Path, typer.Option("--current-window")] = Path(
        "tests/fixtures/monitoring/moderate_drift"
    ),
    baseline: Annotated[Path | None, typer.Option("--baseline")] = None,
    output_dir: Annotated[Path | None, typer.Option("--output-dir")] = None,
    replace: Annotated[bool, typer.Option("--replace")] = False,
) -> None:
    """Run deterministic monitoring against a synthetic current window."""

    try:
        summary = run_monitoring(
            MonitoringConfig.from_file(config_path),
            DriftThresholdConfig.from_file(threshold_config_path),
            current_window=current_window,
            baseline_path=baseline,
            output_dir=output_dir,
            replace=replace,
        )
    except Exception as exc:
        typer.echo(f"Monitoring run failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Monitoring disposition={summary['overall_disposition']} "
        f"warnings={summary['warning_count']} critical={summary['critical_count']}."
    )


@app.command("validate-monitoring")
def validate_monitoring_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/monitoring.yaml"),
    threshold_config_path: Annotated[Path, typer.Option("--threshold-config")] = Path(
        "config/drift_thresholds.yaml"
    ),
) -> None:
    """Validate monitoring evidence and no-action boundaries."""

    del threshold_config_path
    try:
        result = validate_monitoring_evidence(MonitoringConfig.from_file(config_path))
    except Exception as exc:
        typer.echo(f"Monitoring validation failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Monitoring validation passed with {result['alert_count']} alerts and "
        f"disposition={result['review_disposition']}."
    )


@app.command("describe-monitoring")
def describe_monitoring_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/monitoring.yaml"),
) -> None:
    """Describe latest committed monitoring summary."""

    import json

    config = MonitoringConfig.from_file(config_path)
    path = (
        repository_root() / config.outputs.committed_evidence_directory / "monitoring_summary.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    typer.echo(f"Monitoring run: {payload['monitoring_run_identifier']}")
    typer.echo(f"Scenario: {payload['scenario']}")
    typer.echo(f"Disposition: {payload['overall_disposition']}")


@app.command("list-monitoring-alerts")
def list_monitoring_alerts_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/monitoring.yaml"),
) -> None:
    """List latest committed monitoring alerts."""

    import json

    config = MonitoringConfig.from_file(config_path)
    path = (
        repository_root() / config.outputs.committed_evidence_directory / "monitoring_alerts.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    for alert in payload["alerts"]:
        typer.echo(
            f"{alert['alert_id']} {alert['severity']} {alert['category']}: {alert['reason']}"
        )


@app.command("show-monitoring-review")
def show_monitoring_review_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/monitoring.yaml"),
) -> None:
    """Show latest committed monitoring review disposition."""

    import json

    config = MonitoringConfig.from_file(config_path)
    path = (
        repository_root() / config.outputs.committed_evidence_directory / "monitoring_review.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    typer.echo(f"Overall disposition: {payload['overall_disposition']}")
    typer.echo(f"Retraining status: {payload['retraining_status']}")
    typer.echo(f"Registry mutation status: {payload['registry_mutation_status']}")


@app.command("assess-retraining-eligibility")
def assess_retraining_eligibility_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/retraining.yaml"),
) -> None:
    """Assess retraining eligibility without training."""

    try:
        result = assess_eligibility(RetrainingConfig.from_file(config_path))
    except Exception as exc:
        typer.echo(f"Retraining eligibility failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Eligibility: {result['eligibility_result']}")
    typer.echo(f"Reasons: {', '.join(result['reasons']) or 'none'}")


@app.command("prepare-retraining-dataset")
def prepare_retraining_dataset_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/retraining.yaml"),
) -> None:
    """Prepare the governed labelled retraining dataset fixture."""

    try:
        result = prepare_dataset(RetrainingConfig.from_file(config_path))
    except Exception as exc:
        typer.echo(f"Retraining dataset preparation failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Prepared retraining dataset rows={result['eligible_rows']} "
        f"monitoring_run={result['monitoring_run_identifier']}."
    )


@app.command("run-retraining")
def run_retraining_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/retraining.yaml"),
    comparison_config_path: Annotated[Path, typer.Option("--comparison-config")] = Path(
        "config/champion_challenger.yaml"
    ),
    monitoring_run: Annotated[
        str | None, typer.Option("--monitoring-run", help="Expected monitoring run identifier.")
    ] = None,
    labelled_window: Annotated[
        Path | None, typer.Option("--labelled-window", help="Reserved labelled-window override.")
    ] = None,
    output_dir: Annotated[
        Path | None, typer.Option("--output-dir", help="Reserved report-directory override.")
    ] = None,
    candidate_dir: Annotated[
        Path | None, typer.Option("--candidate-dir", help="Reserved candidate-directory override.")
    ] = None,
    replace: Annotated[bool, typer.Option("--replace")] = False,
) -> None:
    """Run controlled retraining and champion-challenger evidence generation."""

    del monitoring_run, labelled_window, output_dir, candidate_dir
    try:
        result = run_retraining(
            RetrainingConfig.from_file(config_path),
            ComparisonConfig.from_file(comparison_config_path),
            replace=replace,
        )
    except Exception as exc:
        typer.echo(f"Retraining run failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Retraining recommendation={result['recommendation']} "
        f"registration_eligible={result['registration_eligible']}."
    )


@app.command("validate-retraining")
def validate_retraining_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/retraining.yaml"),
) -> None:
    """Validate retraining evidence and no-mutation boundaries."""

    try:
        result = validate_retraining_evidence(RetrainingConfig.from_file(config_path))
    except Exception as exc:
        typer.echo(f"Retraining validation failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Retraining validation passed recommendation={result['recommendation']}.")


@app.command("compare-champion-challenger")
def compare_champion_challenger_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/retraining.yaml"),
    comparison_config_path: Annotated[Path, typer.Option("--comparison-config")] = Path(
        "config/champion_challenger.yaml"
    ),
) -> None:
    """Show champion-challenger comparison summary."""

    del config_path, comparison_config_path
    import json

    path = repository_root() / "reports/retraining/champion_challenger_comparison.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    typer.echo(f"Best challenger: {payload['best_challenger_candidate_identifier']}")
    typer.echo(f"Same-row evaluation: {payload['same_row_evaluation_confirmation']}")


@app.command("show-retraining-gates")
def show_retraining_gates_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/retraining.yaml"),
) -> None:
    """Show retraining promotion gate result."""

    del config_path
    import json

    path = repository_root() / "reports/retraining/promotion_gates.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    typer.echo(f"Gate result: {payload['overall_result']}")
    typer.echo(f"Approval not implied: {payload['approval_not_implied']}")


@app.command("show-retraining-recommendation")
def show_retraining_recommendation_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/retraining.yaml"),
) -> None:
    """Show retraining recommendation and model-lifecycle boundaries."""

    del config_path
    import json

    path = repository_root() / "reports/retraining/retraining_recommendation.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    typer.echo(f"Recommendation: {payload['recommendation']}")
    typer.echo(f"Approval status: {payload['approval_status']}")
    typer.echo(f"Activation status: {payload['activation_status']}")
    typer.echo(f"Automatic action: {payload['automatic_action']}")


@app.command("register-retraining-candidate")
def register_retraining_candidate_command(
    recommendation: Annotated[Path, typer.Option("--recommendation")] = Path(
        "reports/retraining/retraining_recommendation.json"
    ),
    registry_config_path: Annotated[Path, typer.Option("--registry-config")] = Path(
        "config/model_registry.yaml"
    ),
    actor: Annotated[str, typer.Option("--actor")] = "LOCAL-RETRAINING-REVIEWER",
    reason: Annotated[str, typer.Option("--reason")] = "Registration-for-review fixture",
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/retraining.yaml"),
) -> None:
    """Create a registration-for-review fixture only when recommendation permits it."""

    del registry_config_path
    try:
        result = register_retraining_candidate_fixture(
            RetrainingConfig.from_file(config_path),
            recommendation,
            actor=actor,
            reason=reason,
        )
    except Exception as exc:
        typer.echo(f"Retraining candidate registration blocked: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Registered fixture version={result['registry_version']} status={result['status']}."
    )


@app.command("verify-retraining")
def verify_retraining_command() -> None:
    """Run deterministic retraining verification script."""

    script = repository_root() / "scripts" / "verify_retraining.py"
    result = subprocess.run([sys.executable, str(script)], cwd=repository_root(), check=False)
    if result.returncode != 0:
        raise typer.Exit(result.returncode)


@app.command("validate-release-config")
def validate_release_config_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/release.yaml"),
) -> None:
    """Validate non-deploying Milestone 13 release configuration."""

    try:
        payload = validate_release_config(ReleaseConfig.from_file(config_path))
    except Exception as exc:
        typer.echo(f"Release config validation failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        "Release config validation passed "
        f"publish_images={payload['publish_images']} cloud_enabled={payload['cloud_enabled']}."
    )


@app.command("build-release-manifest")
def build_release_manifest_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/release.yaml"),
) -> None:
    """Write Milestone 13 release assurance evidence."""

    try:
        result = generate_release_assurance(ReleaseConfig.from_file(config_path), repository_root())
    except Exception as exc:
        typer.echo(f"Release manifest build failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(
        f"Release manifest built tag={result['manifest']['release_tag']} "
        f"local={result['readiness']['local_review_readiness']}."
    )


@app.command("assess-release-readiness")
def assess_release_readiness_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/release.yaml"),
) -> None:
    """Assess local review and operational release readiness."""

    try:
        config = ReleaseConfig.from_file(config_path)
        result = assess_release_readiness(config, repository_root())
    except Exception as exc:
        typer.echo(f"Release readiness assessment failed: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Local review readiness: {result['local_review_readiness']}")
    typer.echo(f"Operational release readiness: {result['operational_release_readiness']}")
    typer.echo("Blocking operational gates: " + ", ".join(result["blocking_gates"]))


@app.command("validate-containers")
def validate_containers_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/release.yaml"),
) -> None:
    """Validate container definitions without publishing or deploying."""

    del config_path
    result = validate_containers(repository_root())
    typer.echo(f"Container validation: {result['status']}")
    if result["status"] != "passed":
        raise typer.Exit(1)


@app.command("describe-release")
def describe_release_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/release.yaml"),
) -> None:
    """Describe the current release manifest without external side effects."""

    manifest = build_release_manifest(ReleaseConfig.from_file(config_path), repository_root())
    typer.echo(f"Project version: {manifest['project_version']}")
    typer.echo(f"Git revision: {manifest['git_revision']}")
    typer.echo(f"API image: {manifest['api_image']}")
    typer.echo(f"R-Shiny image: {manifest['rshiny_image']}")
    typer.echo(f"Remote CI executed: {manifest['remote_ci_executed']}")


@app.command("show-release-gates")
def show_release_gates_command(
    config_path: Annotated[Path, typer.Option("--config")] = Path("config/release.yaml"),
) -> None:
    """Print release gate status."""

    result = assess_release_readiness(ReleaseConfig.from_file(config_path), repository_root())
    typer.echo("Hard gates:")
    for name, passed in result["hard_gates"].items():
        typer.echo(f"- {name}: {passed}")
    typer.echo("Operational gates:")
    for name, passed in result["operational_gates"].items():
        typer.echo(f"- {name}: {passed}")


@app.command("root")
def root() -> None:
    """Print the resolved repository root."""

    typer.echo(str(Path(repository_root())))


if __name__ == "__main__":
    app()
