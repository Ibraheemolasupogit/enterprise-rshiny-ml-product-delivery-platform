#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8019}"
KEY="local-smoke-key-$RANDOM"
LOG_FILE="$(mktemp)"
SMOKE_STATUS=1

cleanup() {
  if [[ "$SMOKE_STATUS" -ne 0 && -s "$LOG_FILE" ]]; then
    echo "FastAPI smoke test log:" >&2
    cat "$LOG_FILE" >&2
  fi
  if [[ -n "${API_PID:-}" ]] && kill -0 "$API_PID" >/dev/null 2>&1; then
    kill "$API_PID" >/dev/null 2>&1 || true
    wait "$API_PID" >/dev/null 2>&1 || true
  fi
  rm -f "$LOG_FILE"
}
trap cleanup EXIT

export MODEL_API_KEY="$KEY"
export SERVING_REVIEW_MODE="true"
export PYTHONPATH="${PYTHONPATH:-src}"

R_EXPR='minor <- strsplit(R.version[["minor"]], "[.]")[[1]][1]; lib <- file.path("renv", "library", "local", paste0("R-", R.version[["major"]], ".", minor)); dir.create(lib, recursive = TRUE, showWarnings = FALSE); .libPaths(c(normalizePath(lib), .libPaths())); source("rshiny/global.R"); client <- api_client_from_env(); record <- synthetic_example_record(); response <- api_predict(client, record); stopifnot(isTRUE(response$ok)); stopifnot(isTRUE(response$data$request$review_mode)); stopifnot("unapproved_model" %in% response$data$request$status); stopifnot("not_for_operational_use" %in% response$data$request$status); cat(response$data$prediction$risk_band, "\n")'

python3 -m uvicorn ml_product.serving.app:app_from_config \
  --factory \
  --host 127.0.0.1 \
  --port "$PORT" \
  >"$LOG_FILE" 2>&1 &
API_PID="$!"

for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${PORT}/health/live" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

curl -fsS "http://127.0.0.1:${PORT}/health/live" >/dev/null

MODEL_API_BASE_URL="http://127.0.0.1:${PORT}" \
MODEL_API_KEY="$KEY" \
SHINY_APP_ENV="local" \
Rscript --vanilla -e "$R_EXPR"

SMOKE_STATUS=0
echo "R-Shiny to FastAPI review-mode smoke test passed."
