# R-Shiny Product

This Shiny application is a local API client for the governed FastAPI scoring service. It does not load Python model artefacts, does not use `reticulate`, and does not query DuckDB for scoring.

Run the API in local review mode first:

```bash
export MODEL_API_KEY="<choose-a-local-key>"
export SERVING_REVIEW_MODE="true"
python3 -m ml_product.cli serve-model-api --registry-config config/model_registry.yaml --serving-config config/serving.yaml
```

Then run Shiny:

```bash
export MODEL_API_BASE_URL="http://127.0.0.1:8000"
export MODEL_API_KEY="<same-local-key>"
export SHINY_APP_ENV="local"
Rscript -e 'shiny::runApp("rshiny", host = "127.0.0.1", port = 3838)'
```

Every prediction is labelled as review mode, unapproved model, synthetic-data prototype, and not for operational or clinical use.
## Advanced Product Scope

Milestone 10 adds synthetic cohort scoring, locked evidence performance review, read-only governance, exportable synthetic cohort results, and stronger error handling. The app still consumes FastAPI only and never loads model artefacts or local DuckDB data for scoring.

Milestone 11 adds a read-only Monitoring page. It displays committed synthetic monitoring evidence for data quality, drift, prediction distributions, labelled performance, calibration, operational status and alerts. The page has no retraining, approval, activation, deployment, rollback, threshold or calibration controls.

The registered model remains pending and inactive. Review mode is local only and not approved for operational or clinical use.
## Release Status

Milestone 13 release status is read-only evidence under `reports/assurance`. The R-Shiny application remains local review software and does not expose deploy, publish, approve, or activate controls.
