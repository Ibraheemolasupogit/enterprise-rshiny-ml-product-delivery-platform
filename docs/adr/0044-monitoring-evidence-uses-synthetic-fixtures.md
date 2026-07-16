# ADR 0044: Monitoring Evidence Uses Synthetic Fixtures

## Status

Accepted.

## Context

The repository is a product-delivery demonstration and must not include real patient data or sensitive operational telemetry.

## Decision

Milestone 11 monitoring evidence is generated from deterministic synthetic fixtures. Reports contain aggregate metrics, statuses, fingerprints and alert metadata. Raw request inputs, patient identifiers, admission identifiers, secrets and absolute workstation paths are prohibited.

## Consequences

Monitoring can be tested and reviewed reproducibly inside the repository while preserving the synthetic-data-only boundary established by earlier milestones.
