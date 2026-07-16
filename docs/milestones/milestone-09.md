# Milestone 9 - Modular R-Shiny MVP

Status: Complete

Milestone 9 implements a modular R-Shiny MVP integrated with the governed local FastAPI scoring service. The Shiny application is an API client only: it does not load model artefacts, does not use `reticulate`, and does not query DuckDB for individual scoring.

Implemented pages:

- Product Overview
- Single Prediction
- User Feedback

Explicitly deferred:

- Cohort scoring
- Advanced performance dashboard
- Monitoring dashboard
- Registry administration
- Retraining, rollback and production release controls

Current model status:

- Registry state: registered
- Approval state: pending
- Activation state: inactive
- Operational serving: unavailable
- Local review mode: available only when the API is started with `SERVING_REVIEW_MODE=true`

Every review-mode prediction is labelled as review mode, unapproved model, synthetic-data prototype and not for operational or clinical use.
