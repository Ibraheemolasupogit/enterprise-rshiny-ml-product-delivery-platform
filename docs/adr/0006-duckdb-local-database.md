# ADR 0006: DuckDB Local Database

## Status

Accepted for Milestone 3.

## Context

The project needs a reproducible relational database without external services.

## Decision

Use DuckDB as the local database baseline.

## Consequences

Builds are local and fast. Future PostgreSQL or Denodo adapters must preserve the same contracts.

## Alternatives Considered

SQLite was less suitable for analytical CSV/Parquet workflows. PostgreSQL was rejected for this milestone because it requires a service.
