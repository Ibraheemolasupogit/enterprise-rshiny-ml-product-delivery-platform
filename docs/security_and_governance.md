# Security and Governance

## Synthetic-Data Restriction

The repository is restricted to synthetic data. Real patient data, NHS data, HMRC data, credentials, and sensitive operational data are prohibited. Milestone 2 source-system samples are generated, not extracted from live systems.

## Secrets

Source control must not contain secrets. `.env.example` contains placeholders only. Runtime secrets will later come from environment variables or approved secret-management tooling.

## Input Validation

Future services must validate inputs at API, configuration, and data-contract boundaries. Milestone 1 validates configuration and repository hygiene only.

## Dependency and Secret Scanning

CI contains foundation checks. Later milestones should add dependency review, software bill of materials, and stronger secret scanning.

## Access, Audit, and Model Governance

Future role-based access, audit logging, data lineage, retention, fairness and bias review, model cards, and promotion evidence will be required before production-like claims. Model promotion requires human approval.

## Milestone 2 Data Controls

Synthetic source data contains no names, NHS identifiers, full addresses, exact postcodes, medical record identifiers, or personnel-level workforce records. Quality defects are intentional fixtures only when recorded in the issue manifest. Clean generation mode produces no intentional defects.

## Milestone 3 Database Controls

The local DuckDB database is generated under ignored paths. Governed views expose quality status and lineage while preserving raw source traceability. The logical-view client disables arbitrary SQL and validates requested views against an allow-list.

## Milestone 4 Denodo Boundary

Real Denodo integration is externally blocked because genuine access is unavailable. The repository keeps the local provider label `denodo_compatible_local` and contains no fabricated Denodo evidence under `denodo/evidence`.

## Milestone 5 Feature Controls

Feature engineering reads only `curated.model_source_view` through the governed client. Direct identifiers, target fields, length-of-stay fields, discharge fields, readmission fields, and outcome fields are excluded from predictors. Generated feature datasets remain ignored, while small committed evidence records leakage, split, registry, and preprocessing metadata.

## Milestone 6 Model Controls

Model development reads only Milestone 5 feature artefacts and evidence. Candidate artefacts remain ignored under `models/candidate`.

## Milestone 7 Registry And Serving Controls

The local registry records immutable metadata and ignored artefact copies. Registration does not grant approval or activation. The FastAPI service requires an approved active model by default and fails closed when no such model exists. Prediction endpoints require a local API key from the environment and do not log full inputs, identifiers, API keys, or outcome values.

## Milestone 8 SAS Viya Boundary

SAS Viya integration is externally blocked because genuine access is unavailable. The local filesystem registry is not represented as SAS Viya and no fake SAS evidence is created.

## Milestone 9 R-Shiny Controls

R-Shiny consumes FastAPI only. It does not load model artefacts, use `reticulate`, query DuckDB for scoring, expose identifiers, expose outcome fields, approve models, activate models or toggle review mode in the UI. Every review-mode prediction is labelled unapproved, synthetic and not for operational or clinical use.
## Milestone 10 Governance Boundary

The Shiny governance page is read-only. It displays pending approval, inactive activation, defer recommendation, review flags, and safe audit information. It provides no approval, rejection, activation, rollback, registration, deployment, monitoring, or retraining controls.

Error handling sanitises API keys, local paths, stack traces, raw payloads, hidden transformed features, identifiers, and outcome fields from user-visible messages and exports.
## Release Governance

Release assurance is local-only in Milestone 13. Workflows and Makefile targets must not push images, deploy cloud resources, create releases, approve models, activate models, or trigger retraining. Operational release is blocked until a model is both approved and active.
