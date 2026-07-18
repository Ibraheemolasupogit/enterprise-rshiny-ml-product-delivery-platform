# Interview Talking Points

## PostgreSQL

PostgreSQL was added to show the production-oriented datastore shape beside DuckDB. DuckDB keeps local tests fast and checkout-safe; PostgreSQL proves schemas, migrations, source loading and governed views can move toward a managed relational backend.

## Denodo

Denodo was added as the governed logical access layer over PostgreSQL. It lets the feature pipeline depend on stable view contracts rather than raw physical tables.

## Logical-View Abstraction

The logical-view client keeps DuckDB, PostgreSQL and Denodo selectable. That boundary prevents feature engineering from knowing where the governed view is physically served.

## Leakage Control

Prediction is made at admission time. Discharge, outcome, identifiers and post-outcome fields are excluded. Leakage checks are committed in `reports/model_evaluation/leakage_report.json`.

## Model Selection

Selection is validation-led and deterministic. Locked test evidence is reported after selection and does not change the candidate. The current candidate is XGBoost for registration review, not approval.

## SAS Viya Role

SAS Viya is a lifecycle provider boundary, not the modelling engine. Python owns feature engineering, model training and evaluation. The provider receives deterministic package and lifecycle metadata.

## Idempotent Registration

Registration uses a fingerprint derived from stable package identity: model name, local version, candidate identifier, source fingerprint, dataset version, model family and artifact checksums. Repeated registration of the same package should reconcile rather than duplicate.

## Champion-Challenger

Champion-challenger comparison combines current champion identity, challenger package identity, evaluation metrics, calibration, fairness, governance state, approval state and compatibility evidence. The current committed state blocks promotion because approval and live external registration are absent.

## Promotion Versus Activation

External promotion updates only external lifecycle state. Local activation remains a separate explicit governed registry action. This prevents a SAS lifecycle event from silently changing the local serving model.

## Monitoring And Retraining

Monitoring compares deterministic synthetic windows to a baseline and writes review evidence. Retraining creates eligibility and recommendation evidence. Neither workflow automatically mutates registry, approval, activation, thresholds or calibration.

## Offline-Safe CI

CI uses local defaults, mocked external clients and optional markers for live services. SAS Viya live calls are not required for CI. Denodo live tests are gated.

## Real NHS Or Enterprise Deployment

A real deployment would need information-governance approval, real data DPIA, production identity and access management, clinical safety review where applicable, data retention controls, service monitoring, incident response, live SAS Viya environment validation, production Denodo governance, signed model-risk approval and change-management records.
