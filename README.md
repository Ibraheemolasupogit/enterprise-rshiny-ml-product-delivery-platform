# Enterprise R-Shiny ML Product Delivery Platform

This repository is the foundation for an enterprise-style analytical product that will demonstrate the full lifecycle of a machine learning decision-support service. The synthetic business scenario is a healthcare operations product that will eventually estimate whether an inpatient admission is likely to result in a stay of seven days or more.

Milestones 1, 2, 3, 5, 6, 7, 9, 10, 11, and 12 are complete. Milestone 4 is externally blocked because genuine Denodo access is unavailable. Milestone 8 is externally blocked because genuine SAS Viya access is unavailable. Milestone 12 adds controlled synthetic retraining review and champion-challenger evidence. The repository still does not include approval, activation, deployment, SAS Viya integration, or real Denodo integration.

## Business Problem

Operational teams often need earlier visibility of admissions that may need additional discharge planning, capacity management, or coordination. The target product will support those workflows by presenting risk signals, supporting context, monitoring evidence, and feedback loops. It is intended for operational decision support, not clinical diagnosis or automated care decisions.

## Intended Users

The target users include operational flow managers, discharge-planning colleagues, performance analysts, data scientists, data engineers, R-Shiny developers, QA analysts, information-governance representatives, platform engineers, service-support analysts, and product owners.

## Synthetic-Data Boundary

All data in this project must be synthetic. Real patient data, NHS data, HMRC data, credentials, commercial screenshots, and sensitive operational records are out of scope. Synthetic data will be introduced in later milestones only.

## Target Architecture

The complete target architecture is:

```text
Synthetic Source Systems
        |
Governed Logical Data Layer
        |
Validation and Entity Linking
        |
Feature Engineering
        |
R and Python Model Development
        |
Model Registry
        |
FastAPI Scoring Service
        |
R-Shiny Operational Application
        |
Monitoring, Feedback and Controlled Retraining
```

The governed logical data layer will be designed so the project can run locally without Denodo while documenting an honest future path for `real_denodo` integration. The model lifecycle will be runnable locally without SAS Viya while documenting an honest future path for `real_sas_viya` integration.

## Planned Product

The R-Shiny product now provides product overview, single synthetic prediction, cohort scoring, locked model-performance evidence, read-only monitoring, read-only retraining review, read-only model governance, and feedback pages. Registry administration, deployment controls, and service handover workflows remain planned for later milestones.

The planned Python lifecycle will cover synthetic data generation, validation, feature engineering, model development, registry management, serving through FastAPI, monitoring, and controlled retraining. Milestone 1 creates only a minimal Python package, settings layer, CLI, and validation tests.

## Commercial-Tool Boundaries

Commercial integration modes must be labelled honestly:

```text
real_denodo
denodo_compatible_local
real_sas_viya
local_model_lifecycle
```

Current status:

```text
Denodo integration: externally blocked and not implemented
SAS Viya integration: externally blocked and not implemented
Local logical-data fallback: implemented with denodo_compatible_local DuckDB views
Local model lifecycle: model development, local registry, governance gates, and local serving implemented
R-Shiny MVP: implemented locally as a FastAPI client
Monitoring: implemented locally with deterministic synthetic evidence and review-only alerts
Controlled retraining review: implemented locally with champion-challenger evidence and no automatic promotion
```

## Local Development Prerequisites

- Python 3.11 or 3.12
- `make`
- R, for local R validation when available
- Git

Install Python development dependencies with:

```bash
python -m pip install -e ".[dev]"
```

Run local quality checks with:

```bash
make quality
```

## Current Implementation Status

Implemented in Milestone 1:

- Repository structure and hygiene files
- Python package foundation
- Configuration placeholders and validation
- R project/package-style foundation
- Product, architecture, governance, delivery, and roadmap documentation
- ADRs
- GitHub collaboration templates
- Basic Python, R-structure, configuration, documentation, and repository validation tests
- CI workflow definitions

Implemented in Milestone 2:

- Deterministic synthetic source-system generators for patients, admissions, diagnoses, ward capacity, workforce, and outcomes
- Small committed CSV and Parquet samples under `data/sample`
- Controlled data-quality fixtures with a machine-readable issue manifest
- Dataset summary and generation manifest metadata
- Data dictionary and Milestone 2 documentation
- CLI and Makefile commands for generation, validation, description, and reproducibility checks
- Automated tests for generation, schemas, quality fixtures, serialisation, CLI, and manifests

Implemented in Milestone 3:

- DuckDB local database build from committed synthetic source files
- Raw, staged, quality, metadata, and curated layers
- Governed logical views for future consumers
- Quality-fixture reconciliation and build evidence
- Provider-neutral logical-view client with DuckDB adapter
- Explicitly unimplemented real Denodo adapter boundary

Milestone 4:

- Externally blocked because genuine Denodo access is unavailable
- No fake Denodo evidence created
- Local provider remains `denodo_compatible_local`

Implemented in Milestone 5:

- Admission-time prediction contract for long-stay decision support
- Reproducible feature engineering from `curated.model_source_view`
- Temporal admission derivations and leakage controls
- Deterministic temporal patient-group train/validation/test split
- Training-only preprocessing fit for imputation, one-hot encoding, and scaling
- Ignored feature datasets under `data/processed/features`
- Committed feature evidence under `reports/model_evaluation`

Implemented in Milestone 6:

- Prevalence and majority-class baselines
- Logistic regression and Random Forest candidate training
- XGBoost candidate training using the official package and local OpenMP runtime
- Validation-led model comparison, calibration, and threshold selection
- Locked test evaluation after selection
- Explainability, fairness, model report, and model card evidence
- Ignored candidate artefacts under `models/candidate`

Implemented in Milestone 7:

- Local filesystem-backed model registry
- Immutable registration of the XGBoost candidate for governance review
- Governance review evidence with a `defer` recommendation
- Explicit approval, activation, retirement, and rollback controls
- Local FastAPI scoring API that fails closed without an approved active model
- Explicit local review mode, disabled by default and not for operational use

Milestone 8:

- Externally blocked because genuine SAS Viya access is unavailable
- No fake SAS Viya screenshots, experiments, registrations, approvals or endpoints created
- Local filesystem registry remains local evidence, not SAS Viya evidence

Implemented in Milestone 9:

- Modular R-Shiny MVP with Product Overview, Single Prediction and User Feedback pages
- Persistent review-mode or scoring-unavailable status banner
- R `httr2` API client for FastAPI prediction and metadata endpoints
- Synthetic-only admission-time prediction form
- Local feedback capture contract under ignored monitoring output
- R tests, smoke test, UAT evidence, docs and ADRs

Implemented in Milestone 10:

- Synthetic cohort scoring through the FastAPI batch contract
- Locked model-performance dashboard from committed evaluation evidence
- Read-only model governance page with pending approval and inactive activation state
- Export contract for synthetic cohort predictions
- Browser-backed Shiny tests, accessibility evidence, docs and ADRs

Implemented in Milestone 11:

- Deterministic monitoring baseline from locked training evidence
- Synthetic current-window fixtures for no drift, drift, schema, missingness, prediction, performance and operational scenarios
- Data quality, schema, numeric drift, categorical drift, missingness, prediction drift, labelled performance, calibration and operational monitoring evidence
- Review-only alerts with no retraining, model replacement, registry mutation, threshold change or calibration change
- Read-only R-Shiny Monitoring page and monitoring UAT evidence

Implemented in Milestone 12:

- Retraining eligibility assessment from monitoring review evidence
- Governed labelled retraining dataset preparation with grouped temporal splitting
- Training-only preprocessing and deterministic challenger model fitting
- Champion scoring, challenger validation, calibration, fairness, stability and gate evidence
- Recommendation engine with a representative `retain_champion` result
- Read-only R-Shiny Retraining Review page

Not implemented:

- Approved active models
- Automatic approval, activation, deployment, Denodo, or SAS Viya integration

## Roadmap

Delivery is milestone based. Current status:

```text
Milestone 1 — Complete
Milestone 2 — Complete
Milestone 3 — Complete
Milestone 4 — Externally blocked
Milestone 5 — Complete
Milestone 6 — Complete
Milestone 7 — Complete
Milestone 8 — Externally blocked
Milestone 9 — Complete
Milestone 10 — Complete
Milestone 11 — Complete
Milestone 12 — Complete
Milestone 13 — Complete
Milestone 14 — Complete
```

Project implementation is complete for portfolio and local review use. External commercial integrations remain blocked, and operational release remains blocked because the registered model is not approved or active.

See [docs/roadmap.md](docs/roadmap.md) for the full roadmap and [docs/milestones/milestone-09.md](docs/milestones/milestone-09.md) for the current milestone.
## Milestone 10 - Advanced R-Shiny Product

The local R-Shiny product now includes Overview, Single Prediction, Cohort Scoring, Model Performance, Model Governance, and Feedback pages. Cohort scoring uses the FastAPI batch endpoint only, performance uses committed model evidence only, and governance is read-only.

Current milestone status: Milestones 1, 2, 3, 5, 6, 7, 9, and 10 are complete; Milestones 4 and 8 are externally blocked; Milestones 11-14 are planned. Monitoring and drift detection are not implemented.
## Milestone 13: CI/CD, Containers And Release Assurance

Milestone 13 adds focused GitHub Actions workflow definitions, local release assurance logic, container packaging, Docker Compose validation, security/dependency/SBOM evidence, and bounded local deployment smoke testing. The repository still has no commits, so remote CI is explicitly recorded as not executed. Local review readiness is available; operational release remains blocked because there is no approved active model.

## Executive Summary

This repository is a governed end-to-end R-Shiny ML product delivery platform for a synthetic healthcare operations use case. It demonstrates product delivery, data engineering, model development, FastAPI serving, R-Shiny user workflows, monitoring, controlled retraining, CI/CD, containers and release assurance without claiming real clinical impact.

## Reviewer Navigation

- Primary architecture: [docs/interview_architecture.md](docs/interview_architecture.md)
- Architecture diagram source: [docs/diagrams/interview-architecture.mmd](docs/diagrams/interview-architecture.mmd)
- Evidence index: [docs/interview_evidence_index.md](docs/interview_evidence_index.md)
- End-to-end lineage: [docs/end_to_end_lineage.md](docs/end_to_end_lineage.md)
- Interview demo guide: [docs/interview_demo_guide.md](docs/interview_demo_guide.md)
- Talking points: [docs/interview_talking_points.md](docs/interview_talking_points.md)
- STAR narrative: [docs/interview_star_narrative.md](docs/interview_star_narrative.md)
- Portfolio capability map: [docs/portfolio_capability_map.md](docs/portfolio_capability_map.md)
- Canonical workflow: [docs/lifecycle_orchestration_demo.md](docs/lifecycle_orchestration_demo.md)
- Repository freeze and final assurance: [docs/repository_freeze.md](docs/repository_freeze.md)
- Known limitations: [docs/limitations.md](docs/limitations.md)

## Product Outcome

The implemented product supports local review of long-stay admission risk evidence. Default operational scoring is unavailable because the model is pending approval and inactive. Explicit review mode is available for demonstration only.

## Architecture

Synthetic source systems flow into DuckDB or PostgreSQL, through Denodo-compatible governed views, feature engineering, model development, local registry and provider-neutral lifecycle controls, FastAPI, R-Shiny, monitoring, controlled retraining review and release assurance. See [docs/interview_architecture.md](docs/interview_architecture.md) for the concise reviewer architecture and [docs/architecture_overview.md](docs/architecture_overview.md) for the broader portfolio overview.

## Technology Stack

Python, R, R-Shiny, FastAPI, DuckDB, XGBoost, scikit-learn, pytest, testthat, Docker Compose, GitHub Actions, Ruff, mypy, SBOM and local release-assurance tooling.

## Repository Structure

Core source lives under `src/ml_product`, R-Shiny code under `rshiny`, configuration under `config`, SQL under `database`, documentation under `docs`, evidence under `reports`, and CI/CD definitions under `.github/workflows`.

## Quick Start

Install Python dependencies with `python3 -m pip install -e ".[dev]"`, restore R dependencies with `make restore-r`, run focused local checks with `python3 -m pytest -q tests/contract`, and run release assurance with `make release-assurance`. For a 10-15 minute walkthrough, use [docs/interview_demo_guide.md](docs/interview_demo_guide.md) rather than rebuilding every artifact.

For final clean-checkout reconstruction and offline-safe assurance, run:

```bash
make final-assurance
```

## Local Review-Mode Runbook

Use `docker compose -f docker-compose.yml -f docker-compose.review.yml up --build` for local review demonstration. Review mode is labelled as unapproved and not for operational use.

## Core Workflows

The Makefile covers validation, reproducibility, PostgreSQL, optional Denodo checks, R-Shiny checks, container checks, smoke tests, lifecycle orchestration, release assurance and final quality gates.

Canonical workflow commands:

```bash
make lifecycle-e2e-local
make lifecycle-e2e-dry-run
make lifecycle-e2e-show
make lifecycle-e2e-validate
```

## Model Results

The recommended registered candidate is XGBoost registry version 1 with sigmoid calibration and threshold `0.75`. Validation evidence supports registration review, while locked-test and fairness limitations remain visible.

## Governance Status

Model approval granted: no. Model activation performed: no. Registry version 1 remains pending and inactive. Retraining recommendation remains `retain_champion`.

## R-Shiny Screenshots Placeholder

Screenshots should be captured only after genuine remote CI is green, following `docs/portfolio_screenshot_runbook.md`. Do not fabricate Denodo or SAS Viya screenshots.

## Monitoring

Monitoring is implemented with deterministic synthetic evidence and review-only alerts. It does not trigger automatic retraining, threshold changes, calibration changes, or registry mutation.

## Retraining

Controlled retraining is implemented as a review workflow. Champion-challenger evidence currently recommends `retain_champion` with no automatic action.

## CI/CD

GitHub Actions cover quality, Python tests, R tests, integration, security, containers and release assurance. Remote CI evidence must come from genuine GitHub runs after push.

## Security Assurance

The repository includes local secret scanning, dependency summaries, SBOM manifest evidence, container validation and CI security workflows. Specialist tools are recorded honestly when unavailable locally.

## Commercial-Tool Boundaries

PostgreSQL: live_validated locally. Denodo: live_validated when the optional local Developer Tier path is enabled; CI remains safe when Denodo is unavailable. SAS Viya client and lifecycle workflows: implemented_and_tested and offline_mock_validated. Live SAS Viya registration and promotion: requires_external_environment. No fabricated commercial evidence is included.

## Limitations

All data are synthetic. The model is not approved or active. Operational release readiness: blocked. External deployment is not performed.

## Milestone Status

Milestones 1, 2, 3, 5, 6, 7, 9, 10, 11, 12, 13, 14 and 15.1-15.5 are complete for local portfolio review. Live SAS Viya execution remains externally blocked until an available environment is provided.

## Interview Relevance

This project is suitable for discussing end-to-end ML product delivery, governance gates, honest external blockers, R-Shiny product design, FastAPI serving, monitoring, retraining and CI/CD release assurance.

## Licence

This project is released under the MIT License.
