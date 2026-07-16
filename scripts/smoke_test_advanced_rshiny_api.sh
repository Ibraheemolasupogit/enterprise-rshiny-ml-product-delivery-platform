#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8020}"
KEY="local-advanced-smoke-key-$RANDOM"
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

R_EXPR='minor <- strsplit(R.version[["minor"]], "[.]")[[1]][1]; lib <- file.path("renv", "library", "local", paste0("R-", R.version[["major"]], ".", minor)); dir.create(lib, recursive = TRUE, showWarnings = FALSE); .libPaths(c(normalizePath(lib), .libPaths())); source("rshiny/global.R"); client <- api_client_from_env(); cfg <- load_app_config(); one <- synthetic_example_record(); single <- api_predict(client, one); stopifnot(isTRUE(single$ok)); stopifnot(isTRUE(single$data$request$review_mode)); stopifnot("unapproved_model" %in% single$data$request$status); data <- synthetic_template_records(); records <- batch_records_from_dataframe(data); response <- api_predict_batch(client, records, cfg); presented <- present_batch_predictions(response, records); stopifnot(isTRUE(presented$ok)); stopifnot(nrow(presented$results) == nrow(data)); stopifnot(identical(presented$results$row_number, seq_len(nrow(data)))); stopifnot(all(presented$results$review_mode)); stopifnot(length(unique(presented$results$model_registry_version)) == 1); stopifnot(all(presented$results$risk_band %in% c("low", "medium", "high"))); summary <- presented$summary; cat(sprintf("batch_rows=%s valid_rows=%s invalid_rows=0 scored_rows=%s high_risk=%s positives=%s mean_probability=%.6f registry_version=%s risk_bands=%s review_mode=%s\n", nrow(data), nrow(data), summary$records_scored, summary$high_risk_count, summary$predicted_positive_count, summary$mean_probability, presented$results$model_registry_version[[1]], paste(presented$results$risk_band, collapse=","), paste(unique(presented$results$review_mode), collapse=",")))'

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
echo "Advanced R-Shiny batch FastAPI smoke test passed."
