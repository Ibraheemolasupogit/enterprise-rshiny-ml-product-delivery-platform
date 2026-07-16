# Data Architecture

The future data architecture starts with deterministic synthetic source systems. Those sources will be validated against contracts, exposed through a governed logical data layer, transformed into features, and used for model development and monitoring.

## Current State

Milestone 2 creates small deterministic synthetic source-system samples for patients, admissions, diagnoses, ward capacity, workforce, and outcomes. It does not create database tables, analytical views, seed data loaders, feature stores, monitoring baselines, or data-quality reports.

Milestone 3 creates a local DuckDB relational source system and governed logical views. The source files remain distinct from curated views, and curated views are not feature-engineering pipelines.

## Governed Logical Data Layer

The governed logical data layer will separate source representation from downstream consumers. Local SQL-compatible views will provide a fallback that can be labelled `denodo_compatible_local`. A genuine Denodo path may be introduced later only with real connection details, tests, and evidence.

## Lineage and Contracts

Future data contracts will define synthetic fields, types, nullable behaviour, and lineage. Every downstream feature and model artefact must trace back to synthetic contracts.

## Quality Fixtures and Reproducibility

The generator supports clean mode and defect-enabled mode. Intentional defects are bounded, deterministic, and recorded in `data/sample/data_quality_issues.json`. The generation manifest records row counts, checksums, configuration fingerprint, dataset version, seed, and synthetic-data declaration. Reproducibility is verified by regenerating into a temporary directory and comparing semantic table content plus stable manifest fields.

## Retention and Safety

Generated synthetic data and monitoring outputs are ignored by default until a milestone deliberately introduces version-controlled fixtures. Real sensitive data is prohibited.
