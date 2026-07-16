# Milestone 3

## Scope

Milestone 3 implements the local database and governed logical data layer using DuckDB. It converts deterministic synthetic source files into raw and staged tables, reconciles quality fixtures, and exposes curated views.

## Date-Range Resolution

The apparent date-range discrepancy was semantic, not a generation bug. Admissions, ward capacity, and workforce records remain inside `2025-01-01` to `2025-03-31`. Discharge outcomes extend to `2025-04-13` because length of stay continues after admission. The manifest now reports configured, admission, ward-capacity, workforce, discharge, and overall observed ranges separately.

## Deliverables

Deliverables include database configuration, SQL contracts, DuckDB build pipeline, quality reconciliation, metadata tables, logical-view client, build evidence, tests, ADRs, and documentation.

## Deferred Work

Real Denodo integration is Milestone 4 and remains unimplemented. Feature engineering, modelling, APIs, R-Shiny behaviour, monitoring, retraining, and deployment remain planned.
