# Local Runbook

## Terminal 1 - API Review Mode

```bash
export MODEL_API_KEY="<choose-a-local-key>"
export SERVING_REVIEW_MODE="true"
python3 -m ml_product.cli serve-model-api --registry-config config/model_registry.yaml --serving-config config/serving.yaml
```

## Terminal 2 - R-Shiny

```bash
export MODEL_API_BASE_URL="http://127.0.0.1:8000"
export MODEL_API_KEY="<same-local-key>"
export SHINY_APP_ENV="local"
Rscript -e 'shiny::runApp("rshiny", host = "127.0.0.1", port = 3838)'
```

Do not commit local keys. Do not use review-mode predictions operationally.
## Advanced R-Shiny Validation

For Milestone 10, run `make test-rshiny-advanced` after restoring R dependencies. The target validates R code, runs unit tests, runs browser-backed `shinytest2`, generates UAT evidence, and executes single and batch FastAPI smoke tests in local review mode.

Use `bash scripts/smoke_test_advanced_rshiny_api.sh` for the bounded batch smoke test. It starts FastAPI on a temporary port and stops it on exit.
