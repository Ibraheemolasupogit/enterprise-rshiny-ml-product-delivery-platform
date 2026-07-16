# Database Architecture

Milestone 3 implements a local DuckDB database at `data/processed/ml_product.duckdb`. The file is generated and ignored by Git; SQL, configuration, evidence, and tests are version-controlled.

## Layers

`raw` mirrors the Milestone 2 source files and preserves intentional quality fixtures with source-row traceability. `staged` applies typed parsing and quality-status columns without silently repairing source values. `quality` records issue manifests, rejected records, ingestion runs, and validation results. `metadata` records dataset, column, relationship, manifest, build, and logical-view inventory. `curated` exposes governed logical views for future consumers.

## Rebuild Strategy

The build validates the Milestone 2 manifest and checksums, creates a temporary DuckDB file, loads raw tables, builds staged tables, reconciles quality fixtures, creates curated views, runs validation checks, writes evidence, and atomically replaces the configured database path.

## Portability

DuckDB is the local baseline because it needs no service and reads CSV/Parquet directly. Future PostgreSQL or Denodo adapters should follow the same raw, staged, quality, metadata, and curated contracts.
