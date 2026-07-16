# Operational Handover

Future operational handover will provide the artefacts needed to support a decision-support product after release.

## Required Artefacts

The future handover pack will include a user guide, technical runbook, data dictionary, model card, monitoring runbook, retraining procedure, rollback procedure, known limitations, support ownership, and incident escalation route.

## Ownership

Product owners approve release readiness. Platform engineering owns runtime and deployment. Service support owns first-line triage. Data scientists own model evidence. Information governance owns boundary review. R-Shiny and Python developers own application and service implementation notes.

## Milestone 1 State

Milestone 1 documents expected handover only. It does not include an operating service, deployed environment, model card, or monitoring runbook because those capabilities do not exist yet.

## Milestone 7 State

Milestone 7 provides a local handover baseline for governance and serving review. Operators can inspect `models/registry.json`, generated registry evidence in `reports/model_evaluation`, and the FastAPI app factory in `ml_product.serving.app`.

## Milestone 9 State

Milestone 9 provides a local R-Shiny MVP for product overview, single synthetic prediction and product feedback. Operators must start FastAPI and Shiny as separate local processes. Review-mode predictions are for technical demonstration only and are not operational or clinical use.

Default serving is not ready until a model is explicitly approved and activated. Local review mode requires `SERVING_REVIEW_MODE=true`, is blocked outside the local environment, and is not for operational use.
## Milestone 10 Handover Note

The R-Shiny product is suitable for local synthetic review only. It includes cohort scoring, evidence review, governance display, and exports, but the registered model is not approved or active. Operational scoring remains unavailable.

Monitoring, drift detection, retraining, promotion, activation, rollback, external deployment, Denodo, and SAS Viya integration are deferred or externally blocked as documented elsewhere.
## Release Handover Boundary

Milestone 13 prepares CI/CD and local deployment evidence but does not perform external handover. Remote CI must be activated by a future first commit and push, and operational release remains blocked until governance approval and activation are completed manually.
