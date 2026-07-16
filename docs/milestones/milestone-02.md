# Milestone 2

## Scope

Milestone 2 implements deterministic synthetic source systems for patients, admissions, diagnoses, ward capacity, workforce, and outcomes. These are separate source-like datasets, not a joined analytical feature table.

## Deliverables

Deliverables include typed configuration, separated generator modules, controlled quality-fixture injection, CSV and Parquet writers, sample data under `data/sample`, metadata manifests, data dictionary, CLI commands, Makefile targets, tests, and reproducibility verification.

## Generation Assumptions

The data is synthetic and non-clinical. Older synthetic patients may have higher comorbidity counts, emergency admissions may have higher acuity, complex broad diagnoses and reduced mobility may increase expected length of stay, and capacity or workforce pressure may moderately affect outcomes. The long-stay target is not generated from a single field and is not intended to represent clinical truth.

## Validation

Validation checks schemas, primary keys, foreign keys, controlled vocabularies, date ranges, outcome consistency, quality-issue manifests, sample files, and reproducibility. Intentional fixtures are allowed only when recorded in `data_quality_issues.json`.

## Known Limitations

The source systems are small committed samples. No database schema, loader, governed logical data layer, features, model, API, R-Shiny behaviour, monitoring, retraining, deployment, Denodo integration, or SAS Viya integration exists.

## Deferred Work

Milestone 3 will introduce the database and governed logical data layer. The Milestone 2 data remains source data only.

## Exit Criteria

Exit requires deterministic generation, successful validation, documented dictionaries, reproducibility evidence, and no real sensitive data or fabricated commercial-tool evidence.
