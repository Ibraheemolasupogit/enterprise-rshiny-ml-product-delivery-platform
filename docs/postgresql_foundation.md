# PostgreSQL Foundation

Milestone 14.1 adds a local PostgreSQL datastore beside the existing DuckDB implementation. DuckDB remains the default backend for local tests, feature builds, model training, serving review mode, and current CI unless PostgreSQL is explicitly selected.

## Local Startup

Set local PostgreSQL credentials in your shell. Do not commit real credentials.

```bash
export DATABASE_BACKEND=postgresql
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5432
export POSTGRES_DB=ml_product
export POSTGRES_USER=ml_product
# Set POSTGRES_PASSWORD locally in your shell or secret manager; do not commit it.
make postgres-start
make postgres-ready
```

The Compose service uses the pinned `postgres:16.10-bookworm` image and stores data in the local `postgres-data` Docker volume.
It is defined in `docker-compose.postgresql.yml` so the canonical application stack in `docker-compose.yml` remains limited to `api` and `rshiny`.

## Migration And Load Commands

```bash
make postgres-migrate
make postgres-load-synthetic-data
make postgres-validate
```

Equivalent CLI commands are:

```bash
python3 -m ml_product.cli postgres-check-readiness --config config/database.yaml
python3 -m ml_product.cli postgres-migrate --config config/database.yaml
python3 -m ml_product.cli postgres-load-synthetic-data --config config/database.yaml
python3 -m ml_product.cli postgres-validate --config config/database.yaml
```

Stop the local service with:

```bash
make postgres-stop
```

Direct Compose usage should also name the PostgreSQL file explicitly:

```bash
docker compose -f docker-compose.postgresql.yml up -d postgres
docker compose -f docker-compose.postgresql.yml stop postgres
```

## Environment Variables

`DATABASE_BACKEND` selects `duckdb` or `postgresql`; unset defaults continue to use DuckDB. PostgreSQL connections are driven by `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`. The password is intentionally not hardcoded in source, configuration, or Compose files.

## Architecture Boundary

DuckDB remains the local file-backed canonical implementation for the current product workflow. PostgreSQL is a production-oriented relational foundation that mirrors the same raw, staged, quality, metadata, and curated logical contracts.

The PostgreSQL migrations create schemas for `raw`, `curated`, `quality`, `registry`, `monitoring`, `feedback`, and `audit`, plus internal `staged` and `metadata` schemas used to preserve the existing DuckDB semantics. Raw PostgreSQL tables do not enforce physical primary keys because the synthetic source fixtures intentionally contain duplicate and rejected-record cases. Duplicate and rejected-record controls remain governed in `quality.rejected_records` and the curated views.

This milestone does not introduce Denodo, deployment automation, feedback workflows, approval changes, or cloud infrastructure.
