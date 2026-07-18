.PHONY: help install-python install-r restore-r lint-python lint-r format-python typecheck-python test-python test-r test-shiny test-shiny-browser run-shiny smoke-test-rshiny-api smoke-test-advanced-rshiny-api validate-rshiny validate-rshiny-advanced test-rshiny test-rshiny-advanced validate-structure validate-config docs-check generate-sample-data validate-sample-data describe-sample-data test-synthetic-data verify-synthetic-data build-database validate-database describe-database list-logical-views postgres-start postgres-ready postgres-migrate postgres-load-synthetic-data postgres-validate postgres-stop denodo-ready denodo-list-views denodo-validate-row-counts denodo-compare-postgresql denodo-sample test-denodo test-database verify-database-build build-features validate-features describe-features list-features show-split-summary check-feature-leakage verify-feature-build test-features train-models validate-models compare-models show-threshold-analysis show-calibration-report show-fairness-report show-candidate-recommendation verify-model-build test-models register-model validate-registry list-models show-governance-review submit-model-for-approval record-approval-decision activate-model validate-serving serve-model-api build-review-artifacts test-registry test-serving build-monitoring-baseline generate-monitoring-fixtures run-monitoring validate-monitoring describe-monitoring list-monitoring-alerts show-monitoring-review verify-monitoring test-monitoring lint-workflows lint-shell lint-docker security-secrets security-python security-dependencies security-container generate-sbom validate-containers build-containers smoke-test-local-deployment validate-release assess-release-readiness show-release-gates release-assurance portfolio-evidence quality quality-full clean

PYTHON ?= python3
R_SETUP ?= minor <- strsplit(R.version[["minor"]], "[.]")[[1]][1]; lib <- file.path("renv", "library", "local", paste0("R-", R.version[["major"]], ".", minor)); dir.create(lib, recursive = TRUE, showWarnings = FALSE); .libPaths(c(normalizePath(lib), .libPaths()))

help:
	@echo "Milestone 1 targets:"
	@echo "  install-python      Install Python development dependencies"
	@echo "  install-r           Check R availability and restore dependencies when available"
	@echo "  restore-r           Restore R dependencies with renv"
	@echo "  lint-r              Run lintr against R-Shiny files"
	@echo "  lint-python         Run Ruff lint checks"
	@echo "  format-python       Run Ruff format checks"
	@echo "  typecheck-python    Run mypy"
	@echo "  test-python         Run pytest"
	@echo "  test-r              Run minimal R tests when R is installed"
	@echo "  validate-structure  Validate repository structure"
	@echo "  validate-config     Validate configuration"
	@echo "  docs-check          Validate documentation presence and boundaries"
	@echo "  generate-sample-data Generate committed synthetic sample data"
	@echo "  validate-sample-data Validate committed synthetic sample data"
	@echo "  describe-sample-data Describe committed synthetic sample data"
	@echo "  test-synthetic-data Run synthetic-data-focused tests"
	@echo "  verify-synthetic-data Verify sample reproducibility"
	@echo "  build-database      Build local DuckDB database"
	@echo "  validate-database   Validate local DuckDB database"
	@echo "  describe-database   Describe database build evidence"
	@echo "  list-logical-views  List governed logical views"
	@echo "  postgres-start      Start local PostgreSQL service"
	@echo "  postgres-ready      Check PostgreSQL readiness"
	@echo "  postgres-migrate    Run PostgreSQL migrations"
	@echo "  postgres-load-synthetic-data Load synthetic source data into PostgreSQL"
	@echo "  postgres-validate   Validate PostgreSQL schemas, counts, and quality controls"
	@echo "  postgres-stop       Stop local PostgreSQL service"
	@echo "  denodo-ready        Check live Denodo readiness"
	@echo "  denodo-list-views   List governed Denodo virtual views"
	@echo "  denodo-validate-row-counts Validate governed Denodo view row counts"
	@echo "  denodo-compare-postgresql Compare Denodo and PostgreSQL populations"
	@echo "  denodo-sample       Read a bounded sample from Denodo"
	@echo "  test-denodo         Run optional Denodo integration tests"
	@echo "  test-database       Run database-focused tests"
	@echo "  verify-database-build Verify deterministic database build"
	@echo "  build-features      Build deterministic Milestone 5 feature datasets"
	@echo "  validate-features   Validate feature outputs and evidence"
	@echo "  describe-features   Describe feature build evidence"
	@echo "  list-features       List transformed features"
	@echo "  show-split-summary  Show deterministic split summary"
	@echo "  check-feature-leakage Run leakage checks without model training"
	@echo "  verify-feature-build Verify deterministic feature builds"
	@echo "  test-features       Run feature-focused tests"
	@echo "  train-models        Train Milestone 6 candidate models"
	@echo "  validate-models     Validate Milestone 6 model evidence"
	@echo "  compare-models      Show validation model comparison"
	@echo "  verify-model-build  Verify deterministic model builds"
	@echo "  test-models         Run model-focused tests"
	@echo "  register-model      Register the Milestone 6 candidate locally"
	@echo "  validate-registry   Validate local registry evidence"
	@echo "  validate-serving    Validate local serving readiness"
	@echo "  build-monitoring-baseline Build Milestone 11 monitoring baseline"
	@echo "  run-monitoring      Run representative synthetic monitoring window"
	@echo "  validate-monitoring Validate committed monitoring evidence"
	@echo "  verify-monitoring   Verify deterministic monitoring evidence"
	@echo "  test-rshiny         Run R-Shiny validation and tests"
	@echo "  smoke-test-rshiny-api Run bounded R client to FastAPI smoke test"
	@echo "  quality             Run all available Milestone 1 through 9 validation"
	@echo "  clean               Remove local Python validation caches"

install-python:
	$(PYTHON) -m pip install -e ".[dev]"

install-r:
	@command -v R >/dev/null 2>&1 || { echo "R is not installed; cannot restore R dependencies locally."; exit 1; }
	Rscript --vanilla -e "if (!requireNamespace('renv', quietly = TRUE)) install.packages('renv', repos = 'https://cloud.r-project.org')"

restore-r: install-r
	Rscript --vanilla -e '$(R_SETUP); renv::restore(prompt = FALSE, library = lib)'

lint-r: restore-r
	Rscript --vanilla -e '$(R_SETUP); lintr::lint_dir("rshiny")'

lint-python:
	$(PYTHON) -m ruff check .

format-python:
	$(PYTHON) -m ruff format --check .

typecheck-python:
	$(PYTHON) -m mypy src

test-python:
	$(PYTHON) -m pytest

test-r: restore-r
	@command -v Rscript >/dev/null 2>&1 || { echo "Rscript is not installed; skipping local R tests is not a pass."; exit 1; }
	Rscript --vanilla -e '$(R_SETUP); testthat::test_dir("rshiny/tests/testthat")'

test-shiny: restore-r
	NOT_CRAN=true Rscript --vanilla -e '$(R_SETUP); if (requireNamespace("shinytest2", quietly = TRUE)) testthat::test_dir("rshiny/tests/shinytest2") else stop("shinytest2 is required")'

test-shiny-browser: test-shiny

run-shiny: restore-r
	Rscript --vanilla -e '$(R_SETUP); shiny::runApp("rshiny", host = "127.0.0.1", port = 3838)'

smoke-test-rshiny-api: restore-r
	bash scripts/smoke_test_rshiny_api.sh

smoke-test-advanced-rshiny-api: restore-r
	bash scripts/smoke_test_advanced_rshiny_api.sh

validate-rshiny:
	$(PYTHON) scripts/validate_rshiny.py
	$(PYTHON) scripts/generate_rshiny_evidence.py

validate-rshiny-advanced: validate-rshiny

test-rshiny: lint-r test-r validate-rshiny smoke-test-rshiny-api

test-rshiny-advanced: lint-r test-r test-shiny-browser validate-rshiny-advanced smoke-test-rshiny-api smoke-test-advanced-rshiny-api

validate-structure:
	$(PYTHON) scripts/validate_repository.py --structure

validate-config:
	$(PYTHON) scripts/validate_repository.py --config

docs-check:
	$(PYTHON) scripts/validate_repository.py --docs

generate-sample-data:
	$(PYTHON) -m ml_product.cli generate-synthetic-data --config config/synthetic_data.yaml

validate-sample-data:
	$(PYTHON) -m ml_product.cli validate-synthetic-data --config config/synthetic_data.yaml

describe-sample-data:
	$(PYTHON) -m ml_product.cli describe-synthetic-data --config config/synthetic_data.yaml

test-synthetic-data:
	$(PYTHON) -m pytest tests/unit/synthetic_data tests/integration/test_synthetic_generation_pipeline.py tests/integration/test_synthetic_cli.py tests/integration/test_sample_data_validation.py tests/contract/test_synthetic_schemas.py tests/contract/test_data_dictionary_coverage.py tests/contract/test_generation_manifest.py

verify-synthetic-data:
	$(PYTHON) scripts/verify_synthetic_data.py

build-database:
	$(PYTHON) -m ml_product.cli build-database --config config/database.yaml --replace

validate-database:
	$(PYTHON) -m ml_product.cli validate-database --config config/database.yaml

describe-database:
	$(PYTHON) -m ml_product.cli describe-database --config config/database.yaml

list-logical-views:
	$(PYTHON) -m ml_product.cli list-logical-views --config config/database.yaml

postgres-start:
	@test -n "$$POSTGRES_PASSWORD" || { echo "POSTGRES_PASSWORD must be set locally."; exit 1; }
	docker compose -f docker-compose.postgresql.yml up -d postgres

postgres-ready:
	$(PYTHON) -m ml_product.cli postgres-check-readiness --config config/database.yaml

postgres-migrate:
	$(PYTHON) -m ml_product.cli postgres-migrate --config config/database.yaml

postgres-load-synthetic-data:
	$(PYTHON) -m ml_product.cli postgres-load-synthetic-data --config config/database.yaml

postgres-validate:
	$(PYTHON) -m ml_product.cli postgres-validate --config config/database.yaml

postgres-stop:
	docker compose -f docker-compose.postgresql.yml stop postgres

denodo-ready:
	$(PYTHON) -m ml_product.cli denodo-check-readiness --config config/database.yaml

denodo-list-views:
	$(PYTHON) -m ml_product.cli denodo-list-views --config config/database.yaml

denodo-validate-row-counts:
	$(PYTHON) -m ml_product.cli denodo-validate-row-counts --config config/database.yaml

denodo-compare-postgresql:
	$(PYTHON) -m ml_product.cli denodo-compare-postgresql --config config/database.yaml

denodo-sample:
	$(PYTHON) -m ml_product.cli denodo-sample --config config/database.yaml --view curated.model_source_view --limit 5

test-denodo:
	DENODO_INTEGRATION_ENABLED=true $(PYTHON) -m pytest tests/integration/test_denodo_integration.py

test-database:
	$(PYTHON) -m pytest tests/unit/ingestion tests/unit/validation tests/unit/linking tests/integration/test_database_build_pipeline.py tests/integration/test_database_cli.py tests/integration/test_curated_views.py tests/integration/test_logical_view_queries.py tests/contract/test_database_schema_contracts.py tests/contract/test_curated_view_contracts.py tests/contract/test_database_evidence.py tests/contract/test_sql_files.py

verify-database-build:
	$(PYTHON) scripts/verify_database_build.py

build-features:
	$(PYTHON) -m ml_product.cli build-features --config config/features.yaml --database-config config/database.yaml --replace

validate-features:
	$(PYTHON) -m ml_product.cli validate-features --config config/features.yaml

describe-features:
	$(PYTHON) -m ml_product.cli describe-features --config config/features.yaml

list-features:
	$(PYTHON) -m ml_product.cli list-features --config config/features.yaml

show-split-summary:
	$(PYTHON) -m ml_product.cli show-split-summary --config config/features.yaml

check-feature-leakage:
	$(PYTHON) -m ml_product.cli check-feature-leakage --config config/features.yaml

verify-feature-build:
	$(PYTHON) scripts/verify_feature_build.py

test-features:
	$(PYTHON) -m pytest tests/unit/features tests/integration/test_feature_build_pipeline.py tests/integration/test_feature_cli.py tests/integration/test_feature_reproducibility.py tests/integration/test_training_only_preprocessing.py tests/contract/test_feature_source_contract.py tests/contract/test_feature_output_contract.py tests/contract/test_feature_registry_contract.py tests/contract/test_split_contract.py tests/contract/test_leakage_report_contract.py

train-models:
	$(PYTHON) -m ml_product.cli train-models --config config/model_training.yaml --threshold-config config/model_thresholds.yaml --replace

validate-models:
	$(PYTHON) -m ml_product.cli validate-models --config config/model_training.yaml --threshold-config config/model_thresholds.yaml

compare-models:
	$(PYTHON) -m ml_product.cli compare-models --config config/model_training.yaml

show-threshold-analysis:
	$(PYTHON) -m ml_product.cli show-threshold-analysis --config config/model_training.yaml

show-calibration-report:
	$(PYTHON) -m ml_product.cli show-calibration-report --config config/model_training.yaml

show-fairness-report:
	$(PYTHON) -m ml_product.cli show-fairness-report --config config/model_training.yaml

show-candidate-recommendation:
	$(PYTHON) -m ml_product.cli show-candidate-recommendation --config config/model_training.yaml

verify-model-build:
	$(PYTHON) scripts/verify_model_build.py

test-models:
	$(PYTHON) -m pytest tests/unit/modelling tests/integration/test_model_training_pipeline.py tests/integration/test_model_cli.py tests/integration/test_model_reproducibility.py tests/integration/test_test_set_lock.py tests/integration/test_candidate_bundle_compatibility.py tests/contract/test_model_training_manifest.py tests/contract/test_model_metrics_contract.py tests/contract/test_threshold_contract.py tests/contract/test_calibration_contract.py tests/contract/test_fairness_contract.py tests/contract/test_candidate_recommendation_contract.py tests/contract/test_model_card_contract.py

register-model:
	$(PYTHON) -m ml_product.cli register-model --registry-config config/model_registry.yaml --model-config config/model_training.yaml --candidate-identifier CAND-85EA9202CAD6FE7F

validate-registry:
	$(PYTHON) -m ml_product.cli validate-registry --config config/model_registry.yaml

list-models:
	$(PYTHON) -m ml_product.cli list-models --config config/model_registry.yaml

show-governance-review:
	$(PYTHON) -m ml_product.cli show-governance-review --config config/model_registry.yaml

submit-model-for-approval:
	$(PYTHON) -m ml_product.cli submit-model-for-approval --model-name long_stay_admission_risk --version 1

record-approval-decision:
	$(PYTHON) -m ml_product.cli record-approval-decision --model-name long_stay_admission_risk --version 1 --decision defer --actor LOCAL-GOVERNANCE-REVIEWER --reason "Synthetic evidence requires further review"

activate-model:
	$(PYTHON) -m ml_product.cli activate-model --model-name long_stay_admission_risk --version 1

validate-serving:
	$(PYTHON) -m ml_product.cli validate-serving --registry-config config/model_registry.yaml --serving-config config/serving.yaml

serve-model-api:
	$(PYTHON) -m ml_product.cli serve-model-api --serving-config config/serving.yaml

build-review-artifacts: validate-sample-data build-database build-features train-models register-model validate-registry validate-serving build-monitoring-baseline
	@test -f models/registered/v000001/xgboost.json || { echo "Missing registered XGBoost artefact: models/registered/v000001/xgboost.json"; exit 1; }
	@test -f monitoring/reports/monitoring_baseline.json || { echo "Missing monitoring baseline: monitoring/reports/monitoring_baseline.json"; exit 1; }

build-monitoring-baseline:
	$(PYTHON) -m ml_product.cli build-monitoring-baseline --config config/monitoring.yaml --threshold-config config/drift_thresholds.yaml --replace

generate-monitoring-fixtures:
	$(PYTHON) -m ml_product.cli generate-monitoring-fixture --scenario no_drift --replace
	$(PYTHON) -m ml_product.cli generate-monitoring-fixture --scenario moderate_drift --replace
	$(PYTHON) -m ml_product.cli generate-monitoring-fixture --scenario severe_drift --replace
	$(PYTHON) -m ml_product.cli generate-monitoring-fixture --scenario schema_failure --replace
	$(PYTHON) -m ml_product.cli generate-monitoring-fixture --scenario missingness_drift --replace
	$(PYTHON) -m ml_product.cli generate-monitoring-fixture --scenario categorical_drift --replace
	$(PYTHON) -m ml_product.cli generate-monitoring-fixture --scenario prediction_drift --replace
	$(PYTHON) -m ml_product.cli generate-monitoring-fixture --scenario performance_degradation --replace
	$(PYTHON) -m ml_product.cli generate-monitoring-fixture --scenario insufficient_labels --replace
	$(PYTHON) -m ml_product.cli generate-monitoring-fixture --scenario operational_degradation --replace

run-monitoring:
	$(PYTHON) -m ml_product.cli run-monitoring --config config/monitoring.yaml --threshold-config config/drift_thresholds.yaml --current-window tests/fixtures/monitoring/moderate_drift --replace

validate-monitoring:
	$(PYTHON) -m ml_product.cli validate-monitoring --config config/monitoring.yaml --threshold-config config/drift_thresholds.yaml

describe-monitoring:
	$(PYTHON) -m ml_product.cli describe-monitoring --config config/monitoring.yaml

list-monitoring-alerts:
	$(PYTHON) -m ml_product.cli list-monitoring-alerts --config config/monitoring.yaml

show-monitoring-review:
	$(PYTHON) -m ml_product.cli show-monitoring-review --config config/monitoring.yaml

verify-monitoring:
	$(PYTHON) scripts/verify_monitoring.py

test-monitoring:
	$(PYTHON) -m pytest tests/unit/monitoring tests/integration/test_monitoring_cli.py tests/contract/test_monitoring_evidence_contract.py

assess-retraining:
	$(PYTHON) -m ml_product.cli assess-retraining-eligibility --config config/retraining.yaml

prepare-retraining-data:
	$(PYTHON) -m ml_product.cli prepare-retraining-dataset --config config/retraining.yaml

run-retraining:
	$(PYTHON) -m ml_product.cli run-retraining --config config/retraining.yaml --comparison-config config/champion_challenger.yaml --replace

validate-retraining:
	$(PYTHON) -m ml_product.cli validate-retraining --config config/retraining.yaml

compare-champion-challenger:
	$(PYTHON) -m ml_product.cli compare-champion-challenger --config config/retraining.yaml --comparison-config config/champion_challenger.yaml

show-retraining-gates:
	$(PYTHON) -m ml_product.cli show-retraining-gates --config config/retraining.yaml

show-retraining-recommendation:
	$(PYTHON) -m ml_product.cli show-retraining-recommendation --config config/retraining.yaml

verify-retraining:
	$(PYTHON) scripts/verify_retraining.py

test-retraining:
	$(PYTHON) -m pytest tests/unit/retraining tests/integration/test_retraining_cli.py tests/integration/test_retraining_registry_non_mutation.py tests/contract/test_champion_challenger_contract.py tests/contract/test_retraining_recommendation_contract.py

test-registry:
	$(PYTHON) -m pytest tests/unit/registry tests/integration/test_registry_workflow.py tests/integration/test_registry_cli.py tests/contract/test_registry_manifest_contract.py tests/contract/test_governance_review_contract.py tests/contract/test_approval_decision_contract.py tests/contract/test_registry_audit_contract.py

test-serving:
	$(PYTHON) -m pytest tests/unit/serving tests/integration/test_serving_api.py tests/integration/test_serving_review_mode.py tests/integration/test_api_prediction_reproducibility.py tests/contract/test_serving_contract.py tests/contract/test_api_schema_contract.py

lint-workflows:
	$(PYTHON) scripts/validate_repository.py --release-workflows

lint-shell:
	$(PYTHON) scripts/validate_repository.py --release-shell

lint-docker:
	$(PYTHON) scripts/validate_repository.py --release-containers

security-secrets:
	$(PYTHON) -m ml_product.cli build-release-manifest --config config/release.yaml
	$(PYTHON) -m pytest tests/contract/test_security_summary_contract.py

security-python:
	@command -v bandit >/dev/null 2>&1 && bandit -r src scripts -ll || echo "bandit not installed locally; CI workflow runs bandit."

security-dependencies:
	@command -v pip-audit >/dev/null 2>&1 && pip-audit --strict || echo "pip-audit not installed locally; CI workflow runs pip-audit."

security-container:
	@command -v trivy >/dev/null 2>&1 && trivy fs --severity HIGH,CRITICAL --exit-code 1 . || echo "trivy not installed locally; CI workflow runs Trivy."

generate-sbom:
	$(PYTHON) -m ml_product.cli build-release-manifest --config config/release.yaml

validate-containers:
	$(PYTHON) -m ml_product.cli validate-containers --config config/release.yaml

build-containers:
	docker build -f infrastructure/docker/Dockerfile.api --build-arg IMAGE_REVISION=uncommitted -t enterprise-ml-product-api:0.1.0-uncommitted .
	docker build -f infrastructure/docker/Dockerfile.rshiny --build-arg IMAGE_REVISION=uncommitted -t enterprise-ml-product-rshiny:0.1.0-uncommitted .

smoke-test-local-deployment:
	bash scripts/smoke_test_local_deployment.sh

validate-release:
	$(PYTHON) -m ml_product.cli validate-release-config --config config/release.yaml

assess-release-readiness:
	$(PYTHON) -m ml_product.cli assess-release-readiness --config config/release.yaml

show-release-gates:
	$(PYTHON) -m ml_product.cli show-release-gates --config config/release.yaml

release-assurance: validate-release validate-containers
	$(PYTHON) -m ml_product.cli build-release-manifest --config config/release.yaml
	$(PYTHON) -m ml_product.cli assess-release-readiness --config config/release.yaml
	$(PYTHON) -m ml_product.cli show-release-gates --config config/release.yaml

portfolio-evidence: release-assurance
	$(PYTHON) scripts/generate_portfolio_evidence.py

quality: lint-python format-python typecheck-python portfolio-evidence test-python test-r validate-rshiny validate-sample-data verify-synthetic-data validate-database verify-database-build validate-features check-feature-leakage verify-feature-build validate-models verify-model-build validate-registry validate-serving validate-monitoring verify-monitoring validate-retraining verify-retraining validate-release validate-structure validate-config docs-check

quality-full: quality test-shiny-browser lint-workflows lint-shell lint-docker security-secrets security-python security-dependencies validate-containers

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage .coverage.* src/ml_product/__pycache__ src/ml_product/*/__pycache__ tests/*/__pycache__ tests/*/*/__pycache__ scripts/__pycache__
