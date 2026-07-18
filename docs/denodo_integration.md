# Denodo Integration

Milestone 14.2 adds an optional live Denodo Developer Tier path over the Milestone 14.1 PostgreSQL datastore. DuckDB remains the default local workflow, PostgreSQL remains available as a direct backend, and Denodo is selected only when explicitly configured.

## Access And Installation

Install or access Denodo Developer Tier using Denodo’s official distribution for your workstation. Enable the Virtual DataPort server and confirm you can connect with Design Studio or the web administration tools. This repository does not install Denodo or commit Denodo credentials.

For Python live validation, use Denodo’s ODBC driver and install the optional Python connector:

```bash
python3 -m pip install -e ".[denodo,dev]"
```

The implemented Python connection method is ODBC through `pyodbc` and `DENODO_ODBC_DSN`. `DENODO_JDBC_URL` is documented for Developer Tier setup and JDBC tooling, but the Python feature pipeline uses ODBC.

## Environment Variables

```bash
export LOGICAL_VIEW_BACKEND=denodo
export DENODO_HOST=127.0.0.1
export DENODO_PORT=9996
export DENODO_DATABASE=ml_product
export DENODO_USER='<set-locally>'
# Set DENODO_PASSWORD locally in your shell or secret manager; do not commit it.
export DENODO_ODBC_DSN='<set-locally>'
export DENODO_JDBC_URL='jdbc:vdb://127.0.0.1:9999/ml_product'
```

For comparison with PostgreSQL, also set:

```bash
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
export POSTGRES_DB=ml_product
export POSTGRES_USER=ml_product
# Set POSTGRES_PASSWORD locally in your shell or secret manager; do not commit it.
```

## PostgreSQL Source Connection

Start and load PostgreSQL first:

```bash
make postgres-start
make postgres-ready
make postgres-migrate
make postgres-load-synthetic-data
make postgres-validate
```

The PostgreSQL service lives in `docker-compose.postgresql.yml`; the `make postgres-*` targets use that file explicitly.

In Denodo Developer Tier, create a PostgreSQL JDBC data source named `ds_postgresql_ml_product` pointing to the local PostgreSQL database. Credentials should be entered through Denodo tooling or secret handling, not committed.

## Virtual View Import

Use the scripts in `database/denodo/vql/` as Developer Tier setup artefacts:

- `010_postgresql_datasource.vql` documents the PostgreSQL source connection.
- `020_base_views.vql` maps PostgreSQL curated objects into Denodo base views.
- `030_governed_virtual_views.vql` exposes the governed virtual views consumed by Python.

Expected governed views:

- `curated.admission_diagnosis_summary`
- `curated.admission_operational_context`
- `curated.daily_ward_operational_context`
- `curated.model_source_view`
- `curated.outcome_context_view`
- `curated.patient_admission_view`

Base views use the `bv_pg_<schema>_<object>` naming convention. Governed views keep the existing curated contract names so the feature pipeline can switch transport without changing feature configuration.

## Validation Commands

```bash
make denodo-ready
make denodo-list-views
make denodo-validate-row-counts
make denodo-compare-postgresql
make denodo-sample
DENODO_INTEGRATION_ENABLED=true python3 -m pytest tests/integration/test_denodo_integration.py
LOGICAL_VIEW_BACKEND=denodo python3 -m ml_product.cli build-features --config config/features.yaml --replace
```

Live Denodo tests are skipped unless `DENODO_INTEGRATION_ENABLED=true` is set.

## Lineage And Access Control

Lineage is PostgreSQL curated source to Denodo base view to Denodo governed virtual view to Python feature pipeline. The Denodo user used by this project should have read-only access to the governed virtual views. Raw PostgreSQL write paths, model approval, feedback workflows, staging, SAS Viya, cloud deployment, and production release remain out of scope.

## Known Limitations

Developer Tier is local and not a production Denodo deployment. The repository cannot validate driver installation, DSN setup, or imported VQL unless a live Denodo instance is available. The VQL files are setup artefacts and should be exported/reconciled from your actual Developer Tier environment when live validation is performed.
