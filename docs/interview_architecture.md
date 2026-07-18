# Interview Architecture

This is the primary 10-15 minute architecture entry point for the portfolio. It summarises the implemented product and links to detailed evidence rather than replacing the existing documentation set.

## Business Problem

The product demonstrates how a healthcare operations team could review synthetic long-stay admission risk evidence before considering operational use. The data are fully synthetic and the repository makes no real clinical-impact claim.

The prediction target is `long_stay_flag`: whether an inpatient admission has a length of stay of seven days or more. The prediction point is admission-time review using demographics, admission context, diagnosis summary and ward operational context that are available at or shortly after admission. Outcome and discharge fields are excluded from predictors.

Primary users are bed-management, operational flow, analytics, model-risk and platform teams. The supported decision is review of operational planning evidence, not automated clinical decision-making.

## Component Architecture

See the source-controlled diagram in [docs/diagrams/interview-architecture.mmd](diagrams/interview-architecture.mmd).

The end-to-end path is:

1. Synthetic source data and contracts.
2. DuckDB for the default local analytical build and PostgreSQL as the production-oriented datastore foundation.
3. Denodo governed virtual views over PostgreSQL for the enterprise logical-view path.
4. Provider-neutral logical-view client feeding leakage-safe feature engineering.
5. Python model training, validation, calibration, thresholding, fairness and explainability evidence.
6. Local registry and provider-neutral lifecycle boundary.
7. Optional SAS Viya-compatible provider for package, registration, metadata reconciliation and promotion workflows.
8. Approval and promotion gates.
9. Explicit local activation, separate from external promotion.
10. FastAPI review-mode serving and R Shiny product interface.
11. Monitoring, retraining review and release assurance.
12. Canonical lifecycle orchestration that records resumable evidence without mutating approval or activation state.

## Data Plane

The data plane moves records and governed analytical views:

- Synthetic source data: `data/sample/*.csv`, `data/sample/*.parquet`, `data/sample/generation_manifest.json`.
- DuckDB local implementation: `config/database.yaml`, `database/schema`, `database/views`.
- PostgreSQL foundation: `docker-compose.postgresql.yml`, `database/postgresql/migrations`, `src/ml_product/ingestion/postgresql.py`.
- Denodo virtual layer: `database/denodo/vql`, `src/ml_product/ingestion/denodo_client.py`.
- Governed model source: `curated.model_source_view`, configured in `config/features.yaml`.
- Feature evidence: `reports/model_evaluation/feature_build_manifest.json`.

DuckDB remains the default checkout-safe path for local tests unless an explicit PostgreSQL or Denodo mode is selected.

## Control Plane

The control plane decides what may happen:

- Model selection is validation-led, not test-set-led.
- Registration does not imply approval.
- Approval is human-governed and currently pending.
- External SAS Viya promotion is separate from local activation.
- Local activation is explicit and uses the existing registry command only.
- Monitoring and retraining create review evidence, not automatic lifecycle mutation.
- Release assurance distinguishes local review readiness from operational release readiness.

The canonical workflow runner in `src/ml_product/lifecycle/orchestration.py` sequences the control plane without replacing existing registry, governance, activation, rollback, monitoring or release logic.

## Evidence Plane

The evidence plane is the audit trail:

- Data quality: `reports/data_quality`.
- Feature and model evidence: `reports/model_evaluation`.
- Registry and governance evidence: `models/registry.json`, `reports/model_evaluation/model_registry_manifest.json`, `reports/model_evaluation/approval_decision.json`.
- Monitoring evidence: `reports/monitoring`.
- Release and security assurance: `reports/assurance`.
- Portfolio evidence: `reports/portfolio`.
- Lifecycle workflow evidence location: `reports/model_evaluation/lifecycle_workflows`, generated locally and not required as committed runtime evidence.

The evidence index is [docs/interview_evidence_index.md](interview_evidence_index.md).

## Modes

`local_safe` is the default interview path. It uses the local provider, committed evidence and generated local artifacts. It does not contact external services.

`enterprise_dry_run` exercises the enterprise-shaped lifecycle sequence while forcing external registration, external promotion and local activation mutation flags off.

`enterprise_live` is reserved for explicit live-provider operations. PostgreSQL and Denodo have local live-validation paths. SAS Viya-compatible package, registration, reconciliation and promotion workflows are implemented and mock-tested, but live SAS Viya registration and promotion require an available SAS Viya environment.

## Mutation Boundaries

External promotion never activates the local model. Local activation never happens implicitly after external promotion. R Shiny pages are read-only for governance, monitoring and retraining. Monitoring and retraining recommendations do not approve, activate, promote, roll back or deploy a model.

## Governance Gates

The committed model is registry version `1`, candidate `CAND-85EA9202CAD6FE7F`, pending approval and inactive. Operational release remains blocked. Local review-mode serving is available only as labelled demonstration behaviour.

## Failure Recovery

The lifecycle workflow writes resumable state with configuration and package fingerprints. Resume is allowed only when fingerprints still match. Material configuration or package changes require a fresh run or an explicit restart stage.

## Security Boundaries

No credentials are committed. Environment variable names are documented without values. API keys and SAS Viya authentication material are read from the environment. CI and container workflows are designed to avoid external deployment side effects.

## Known Limitations

- Synthetic data only; no real patient data and no clinical-performance claim.
- Local PostgreSQL and Denodo validation prove integration shape, not production scale.
- Live SAS Viya registration and promotion require external environment access.
- The candidate remains unapproved and inactive.
- Remote CI evidence must be generated only from real GitHub Actions runs after push.

Detailed docs: [docs/postgresql_foundation.md](postgresql_foundation.md), [docs/denodo_integration.md](denodo_integration.md), [docs/sas_viya_integration.md](sas_viya_integration.md), [docs/lifecycle_orchestration_demo.md](lifecycle_orchestration_demo.md), [docs/release_assurance.md](release_assurance.md).
