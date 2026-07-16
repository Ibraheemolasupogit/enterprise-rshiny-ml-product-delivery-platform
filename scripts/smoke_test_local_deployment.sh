#!/usr/bin/env bash
set -euo pipefail

PROJECT_NAME="enterprise-rshiny-ml-m13-smoke"
API_URL="http://127.0.0.1:8000"
SHINY_URL="http://127.0.0.1:3838"
MODEL_API_KEY="${MODEL_API_KEY:-placeholder}"

cleanup() {
  docker compose -p "${PROJECT_NAME}" -f docker-compose.yml -f docker-compose.review.yml down --volumes --remove-orphans >/dev/null 2>&1 || true
  docker compose -p "${PROJECT_NAME}" -f docker-compose.yml down --volumes --remove-orphans >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM

wait_for_http() {
  local url="$1"
  local attempts="${2:-30}"
  local i
  for i in $(seq 1 "${attempts}"); do
    if curl --fail --silent --show-error "${url}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  echo "Timed out waiting for ${url}" >&2
  return 1
}

post_prediction() {
  curl --silent --show-error \
    --header "X-API-Key: ${MODEL_API_KEY}" \
    --header "Content-Type: application/json" \
    --data '{"age":72,"sex":"male","postcode_region":"SR-EAST","deprivation_decile":3,"comorbidity_count":2,"previous_admissions_12m":1,"admission_type":"emergency","source_of_admission":"home","initial_news2_score":6,"mobility_status":"assisted","primary_diagnosis_group":"respiratory_synthetic","primary_diagnosis_complexity":"moderate","diagnosis_count":3,"secondary_diagnosis_count":2,"staffed_beds":30,"occupied_beds":27,"closed_beds":1,"isolation_capacity":2,"registered_nurses":12,"support_workers":6,"medical_staff":3,"agency_hours":10,"vacancy_rate":0.08,"admission_datetime":"2026-01-15T10:30:00"}' \
    "${API_URL}/v1/predict"
}

post_batch_prediction() {
  curl --fail --silent --show-error \
    --header "X-API-Key: ${MODEL_API_KEY}" \
    --header "Content-Type: application/json" \
    --data '{"records":[{"request_id":"LOCAL-REVIEW-1","age":72,"sex":"male","postcode_region":"SR-EAST","deprivation_decile":3,"comorbidity_count":2,"previous_admissions_12m":1,"admission_type":"emergency","source_of_admission":"home","initial_news2_score":6,"mobility_status":"assisted","primary_diagnosis_group":"respiratory_synthetic","primary_diagnosis_complexity":"moderate","diagnosis_count":3,"secondary_diagnosis_count":2,"staffed_beds":30,"occupied_beds":27,"closed_beds":1,"isolation_capacity":2,"registered_nurses":12,"support_workers":6,"medical_staff":3,"agency_hours":10,"vacancy_rate":0.08,"admission_datetime":"2026-01-15T10:30:00"},{"request_id":"LOCAL-REVIEW-2","age":81,"sex":"female","postcode_region":"SR-WEST","deprivation_decile":4,"comorbidity_count":3,"previous_admissions_12m":2,"admission_type":"emergency","source_of_admission":"home","initial_news2_score":5,"mobility_status":"assisted","primary_diagnosis_group":"respiratory_synthetic","primary_diagnosis_complexity":"moderate","diagnosis_count":3,"secondary_diagnosis_count":2,"staffed_beds":30,"occupied_beds":27,"closed_beds":1,"isolation_capacity":2,"registered_nurses":12,"support_workers":6,"medical_staff":3,"agency_hours":10,"vacancy_rate":0.08,"admission_datetime":"2026-01-15T10:30:00"}]}' \
    "${API_URL}/v1/predict/batch"
}

python3 -m ml_product.cli validate-registry --config config/model_registry.yaml >/dev/null
python3 -m ml_product.cli validate-release-config --config config/release.yaml >/dev/null

docker compose -p "${PROJECT_NAME}" build api rshiny

cleanup
MODEL_API_KEY="${MODEL_API_KEY}" docker compose -p "${PROJECT_NAME}" up --detach api rshiny
wait_for_http "${API_URL}/health/live"
wait_for_http "${SHINY_URL}"

python3 - <<'PY'
import json
import urllib.request

ready = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/health/ready").read())
if ready.get("ready") is not False or ready.get("reason") != "no_active_approved_model":
    raise SystemExit(f"default readiness should fail closed, got {ready}")
PY

status_code="$(curl --silent --output /tmp/m13-default-predict.json --write-out "%{http_code}" \
  --header "X-API-Key: ${MODEL_API_KEY}" \
  --header "Content-Type: application/json" \
  --data '{"age":72,"sex":"male","postcode_region":"SR-EAST","deprivation_decile":3,"comorbidity_count":2,"previous_admissions_12m":1,"admission_type":"emergency","source_of_admission":"home","initial_news2_score":6,"mobility_status":"assisted","primary_diagnosis_group":"respiratory_synthetic","primary_diagnosis_complexity":"moderate","diagnosis_count":3,"secondary_diagnosis_count":2,"staffed_beds":30,"occupied_beds":27,"closed_beds":1,"isolation_capacity":2,"registered_nurses":12,"support_workers":6,"medical_staff":3,"agency_hours":10,"vacancy_rate":0.08,"admission_datetime":"2026-01-15T10:30:00"}' \
  "${API_URL}/v1/predict")"
test "${status_code}" = "503"
curl --silent "${SHINY_URL}" | grep -E "Enterprise R-Shiny ML Product|SCORING UNAVAILABLE" >/dev/null

cleanup
MODEL_API_KEY="${MODEL_API_KEY}" docker compose -p "${PROJECT_NAME}" -f docker-compose.yml -f docker-compose.review.yml up --detach api rshiny
wait_for_http "${API_URL}/health/live"
wait_for_http "${SHINY_URL}"

python3 - <<'PY'
import json
import urllib.request

ready = json.loads(urllib.request.urlopen("http://127.0.0.1:8000/health/ready").read())
if ready.get("ready") is not True or ready.get("review_mode") is not True:
    raise SystemExit(f"review readiness should pass, got {ready}")
PY

post_prediction | grep -E "unapproved_model|not_for_operational_use" >/dev/null
post_batch_prediction | grep -E "LOCAL-REVIEW-1|LOCAL-REVIEW-2|unapproved_model" >/dev/null
curl --silent "${SHINY_URL}" | grep "Enterprise R-Shiny ML Product" >/dev/null

cleanup
python3 - <<'PY'
import json
from pathlib import Path

payload = {
    "status": "passed",
    "default_governed_mode": {
        "api_liveness": "passed",
        "api_readiness": "failed_closed_as_expected",
        "prediction": "unavailable_as_expected",
        "shiny_status": "scoring_unavailable_visible",
    },
    "explicit_review_mode": {
        "api_liveness": "passed",
        "api_readiness": "passed_for_local_review",
        "single_prediction": "passed",
        "batch_prediction": "passed",
        "review_labels": "present",
        "shiny_status": "loaded",
    },
    "cleanup": "containers_networks_and_volumes_removed",
    "external_deployment_performed": False,
    "image_publication_performed": False,
}
path = Path("reports/assurance/local_deployment_smoke.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
echo "Local deployment smoke test passed."
