# API Contract

Endpoints:

- `GET /health/live`: public liveness only.
- `GET /health/ready`: readiness, including model availability.
- `GET /v1/model`: authenticated safe model metadata.
- `POST /v1/predict`: authenticated single-record scoring.
- `POST /v1/predict/batch`: authenticated bounded batch scoring.
- `GET /v1/registry/status`: authenticated registry status.

Inputs are raw admission-time predictors such as age, sex, postcode region, deprivation decile, admission source/type, acuity, diagnosis counts, operational capacity, staffing context, and admission datetime. Outcome fields and patient/admission identifiers are rejected.

Responses include probability, thresholded class, risk band, model metadata, explanation summary, limitations, request id, and review-mode status.

The R-Shiny MVP consumes this contract through `httr2`. It sends no identifiers or outcome fields and requires review-mode responses to include `review_mode`, `unapproved_model`, and `not_for_operational_use` status labels.
