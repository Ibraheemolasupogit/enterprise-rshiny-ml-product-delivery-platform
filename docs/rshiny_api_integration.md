# R-Shiny API Integration

The R API client uses `httr2` and sends `X-API-Key` to authenticated FastAPI endpoints. It uses bounded timeouts and maps authentication, validation, service unavailable, network and malformed-response errors to safe user-facing messages.

Prediction endpoint:

```text
POST /v1/predict
```

The request contains admission-time synthetic predictors only. It excludes patient identifiers, admission identifiers, outcomes, discharge fields and readmission outcomes.

The response parser expects:

- `prediction`
- `model`
- `explanation`
- `limitations`
- `request`

Review-mode responses must include `review_mode`, `unapproved_model` and `not_for_operational_use` labels.
## Batch Endpoint

Milestone 10 adds R client support for `POST /v1/predict/batch`. The request body is `{ "records": [...] }` where every record matches the single-prediction raw predictor contract. The R parser requires response count and request order to match, review-mode labels to be present, and registry version to be consistent within the batch.

There is no direct model-file loading, DuckDB query, reticulate scoring, or repeated-single fallback in the Shiny app.
