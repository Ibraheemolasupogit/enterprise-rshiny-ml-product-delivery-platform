# Milestone 1

## Scope

Milestone 1 establishes the product foundation only. It creates repository hygiene, directory layout, Python and R foundations, configuration placeholders, documentation, ADRs, collaboration templates, validation scripts, tests, and CI workflow definitions.

## Deliverables

Deliverables include root project files, `src/ml_product`, R package-style files, planned directories, YAML configuration, product and architecture docs, ADRs, GitHub templates, Python tests, R foundation tests, and repository validation.

## Architecture Decisions

The platform is milestone based, synthetic-data only, Python and R responsibilities are separated, commercial-tool integrations require honest labelling, and model promotion will require human approval.

## Validation

Local validation should run Python linting, formatting checks, mypy, pytest, repository validation, `make quality`, and R tests when R is installed.

## Known Limitations

No data, database tables, views, features, models, APIs, R-Shiny behaviour, monitoring, retraining, deployment, Denodo, or SAS Viya integration exists in Milestone 1.

## Deferred Work

Milestone 2 will introduce deterministic synthetic source systems. All other product capabilities remain planned.

## Exit Criteria

Exit requires local checks attempted, documentation aligned with scope, no real sensitive data, no generated model or dataset artefacts, and no false completion claims.
