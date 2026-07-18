"""Validate Milestone 1 through 11 repository structure, configuration, docs, and boundaries."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ROOT_FILES = [
    "README.md",
    "LICENSE",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    ".env.example",
    ".dockerignore",
    "Makefile",
    "pyproject.toml",
    "requirements-dev.txt",
    "renv.lock",
    ".Rprofile",
    "DESCRIPTION",
    "docker-compose.yml",
]

REQUIRED_DIRECTORIES = [
    "config",
    "config/environments",
    "data/raw",
    "data/staged",
    "data/processed",
    "data/monitoring",
    "data/sample",
    "data/reference",
    "database/schema",
    "database/views",
    "database/seeds",
    "database/validation",
    "denodo/virtual_views",
    "denodo/queries",
    "denodo/evidence",
    "sas_viya/programs",
    "sas_viya/model_evidence",
    "src/ml_product/synthetic_data",
    "src/ml_product/ingestion",
    "src/ml_product/validation",
    "src/ml_product/linking",
    "src/ml_product/features",
    "src/ml_product/modelling",
    "src/ml_product/registry",
    "src/ml_product/serving",
    "src/ml_product/monitoring",
    "src/ml_product/retraining",
    "src/ml_product/release",
    "src/ml_product/utils",
    "rshiny/R",
    "rshiny/modules",
    "rshiny/tests/testthat",
    "rshiny/tests/shinytest2",
    "rshiny/www",
    "models/candidate",
    "models/approved",
    "models/archived",
    "monitoring/baseline",
    "monitoring/current",
    "monitoring/alerts",
    "monitoring/reports",
    "reports/data_quality",
    "reports/model_evaluation",
    "reports/monitoring",
    "reports/uat",
    "reports/assurance",
    "reports/sample",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "tests/end_to_end",
    "tests/fixtures",
    "scripts",
    "infrastructure/docker",
    "infrastructure/deployment",
    "docs/adr",
    "docs/diagrams",
    "docs/milestones",
    ".github/ISSUE_TEMPLATE",
    ".github/workflows",
]

REQUIRED_DOCS = [
    "docs/product_vision.md",
    "docs/user_personas.md",
    "docs/user_journeys.md",
    "docs/mvp_scope.md",
    "docs/architecture.md",
    "docs/data_architecture.md",
    "docs/working_together_delivery_model.md",
    "docs/product_backlog.md",
    "docs/testing_strategy.md",
    "docs/ci_cd_strategy.md",
    "docs/security_and_governance.md",
    "docs/denodo_integration.md",
    "docs/sas_viya_integration.md",
    "docs/operational_handover.md",
    "docs/limitations.md",
    "docs/roadmap.md",
    "docs/milestones/milestone-01.md",
    "docs/milestones/milestone-02.md",
    "docs/data_dictionary.md",
    "docs/database_architecture.md",
    "docs/governed_logical_layer.md",
    "docs/data_quality_treatment.md",
    "docs/entity_linking.md",
    "docs/data_lineage.md",
    "docs/local_logical_view_client.md",
    "docs/feature_engineering.md",
    "docs/prediction_contract.md",
    "docs/target_leakage_controls.md",
    "docs/dataset_splitting.md",
    "docs/feature_registry.md",
    "docs/model_development.md",
    "docs/model_evaluation.md",
    "docs/calibration_strategy.md",
    "docs/threshold_selection.md",
    "docs/model_explainability.md",
    "docs/fairness_assessment.md",
    "docs/model_selection.md",
    "docs/model_registry.md",
    "docs/model_governance.md",
    "docs/model_approval.md",
    "docs/model_serving.md",
    "docs/api_contract.md",
    "docs/api_security.md",
    "docs/model_rollback.md",
    "docs/rshiny_architecture.md",
    "docs/rshiny_user_guide.md",
    "docs/rshiny_developer_guide.md",
    "docs/rshiny_api_integration.md",
    "docs/rshiny_accessibility.md",
    "docs/rshiny_feedback.md",
    "docs/rshiny_cohort_scoring.md",
    "docs/rshiny_model_performance.md",
    "docs/rshiny_model_governance.md",
    "docs/rshiny_exports.md",
    "docs/rshiny_error_handling.md",
    "docs/monitoring_architecture.md",
    "docs/monitoring_baseline.md",
    "docs/data_quality_monitoring.md",
    "docs/feature_drift.md",
    "docs/prediction_drift.md",
    "docs/model_performance_monitoring.md",
    "docs/calibration_monitoring.md",
    "docs/operational_monitoring.md",
    "docs/monitoring_alerts.md",
    "docs/monitoring_review_process.md",
    "docs/rshiny_monitoring.md",
    "docs/retraining_governance.md",
    "docs/champion_challenger.md",
    "docs/retraining_review_page.md",
    "docs/cicd_architecture.md",
    "docs/github_actions.md",
    "docs/release_assurance.md",
    "docs/container_architecture.md",
    "docs/local_container_deployment.md",
    "docs/security_scanning.md",
    "docs/dependency_assurance.md",
    "docs/sbom.md",
    "docs/release_versioning.md",
    "docs/release_gates.md",
    "docs/first_commit_runbook.md",
    "docs/ci_activation_runbook.md",
    "docs/local_runbook.md",
    "docs/milestones/milestone-03.md",
    "docs/milestones/milestone-04.md",
    "docs/milestones/milestone-05.md",
    "docs/milestones/milestone-06.md",
    "docs/milestones/milestone-07.md",
    "docs/milestones/milestone-08.md",
    "docs/milestones/milestone-09.md",
    "docs/milestones/milestone-10.md",
    "docs/milestones/milestone-11.md",
    "docs/milestones/milestone-12.md",
    "docs/milestones/milestone-13.md",
    "docs/adr/0001-milestone-based-delivery.md",
    "docs/adr/0002-python-r-service-boundary.md",
    "docs/adr/0003-synthetic-data-only.md",
    "docs/adr/0004-commercial-tool-fallbacks.md",
    "docs/adr/0005-model-promotion-requires-human-approval.md",
    "docs/adr/0006-duckdb-local-database.md",
    "docs/adr/0007-layered-data-architecture.md",
    "docs/adr/0008-governed-views-over-raw-access.md",
    "docs/adr/0009-quality-fixtures-are-reconciled-not-silently-fixed.md",
    "docs/adr/0010-provider-neutral-logical-view-client.md",
    "docs/adr/0011-admission-time-prediction-contract.md",
    "docs/adr/0012-temporal-patient-group-splitting.md",
    "docs/adr/0013-training-only-preprocessing-fit.md",
    "docs/adr/0014-explicit-target-leakage-registry.md",
    "docs/adr/0015-feature-registry-and-stable-output-contract.md",
    "docs/adr/0016-validation-led-model-selection.md",
    "docs/adr/0017-test-set-lock.md",
    "docs/adr/0018-probability-calibration-before-serving.md",
    "docs/adr/0019-operational-threshold-selection.md",
    "docs/adr/0020-fairness-evidence-is-exploratory-not-certification.md",
    "docs/adr/0021-candidate-models-remain-unregistered.md",
    "docs/adr/0022-local-filesystem-model-registry.md",
    "docs/adr/0023-registration-does-not-equal-approval.md",
    "docs/adr/0024-human-approval-before-activation.md",
    "docs/adr/0025-serving-fails-closed-without-active-model.md",
    "docs/adr/0026-raw-input-api-contract-with-registered-preprocessor.md",
    "docs/adr/0027-local-review-mode-is-not-production-serving.md",
    "docs/adr/0028-immutable-model-versions-and-audited-rollback.md",
    "docs/adr/0029-rshiny-consumes-fastapi-not-model-files.md",
    "docs/adr/0030-review-mode-status-is-always-visible.md",
    "docs/adr/0031-no-identifiers-or-outcome-fields-in-shiny-input.md",
    "docs/adr/0032-renv-for-r-dependency-reproducibility.md",
    "docs/adr/0033-feedback-is-product-feedback-not-clinical-outcome.md",
    "docs/adr/0034-no-ui-governance-bypass.md",
    "docs/adr/0035-cohort-scoring-uses-fastapi-batch-endpoint.md",
    "docs/adr/0036-uploaded-synthetic-data-is-not-retained.md",
    "docs/adr/0037-performance-dashboard-uses-locked-evidence.md",
    "docs/adr/0038-model-governance-view-is-read-only.md",
    "docs/adr/0039-validation-test-degradation-remains-visible.md",
    "docs/adr/0040-browser-backed-shiny-tests-required.md",
    "docs/adr/0041-export-contract-excludes-sensitive-and-hidden-fields.md",
    "docs/adr/0042-monitoring-is-review-only.md",
    "docs/adr/0043-prediction-drift-is-not-performance-drift.md",
    "docs/adr/0044-monitoring-evidence-uses-synthetic-fixtures.md",
    "docs/adr/0045-rshiny-monitoring-is-read-only.md",
    "docs/adr/0046-performance-monitoring-requires-labels.md",
    "docs/adr/0047-monitoring-does-not-change-thresholds-or-calibration.md",
    "docs/adr/0048-operational-logs-exclude-raw-inputs.md",
    "docs/adr/0049-retraining-requires-labels-and-review.md",
    "docs/adr/0050-champion-challenger-does-not-imply-promotion.md",
    "docs/adr/0051-rshiny-retraining-review-is-read-only.md",
    "docs/adr/0057-ci-workflows-have-no-external-deployment-side-effects.md",
    "docs/adr/0058-container-images-separate-api-and-rshiny.md",
    "docs/adr/0059-model-binaries-are-generated-or-mounted-not-committed.md",
    "docs/adr/0060-operational-release-requires-approved-active-model.md",
    "docs/adr/0061-local-review-release-is-not-operational-release.md",
    "docs/adr/0062-sboms-and-security-scans-are-release-gates.md",
    "docs/adr/0063-first-commit-precedes-genuine-remote-ci-evidence.md",
    "docs/adr/0064-no-automatic-release-or-image-publication.md",
]

REQUIRED_CONFIGS = [
    "config/settings.yaml",
    "config/data_contracts.yaml",
    "config/features.yaml",
    "config/model_training.yaml",
    "config/model_thresholds.yaml",
    "config/model_registry.yaml",
    "config/model_governance.yaml",
    "config/model_lifecycle.yaml",
    "config/serving.yaml",
    "config/rshiny.yaml",
    "config/monitoring.yaml",
    "config/drift_thresholds.yaml",
    "config/retraining.yaml",
    "config/champion_challenger.yaml",
    "config/release.yaml",
    "config/deployment.yaml",
    "config/synthetic_data.yaml",
    "config/database.yaml",
    "config/environments/development.yaml",
    "config/environments/staging.yaml",
    "config/environments/production.yaml",
]

VALID_INTEGRATION_MODES = {
    "not_implemented",
    "real_denodo",
    "denodo_compatible_local",
    "real_sas_viya",
    "local_model_lifecycle",
}

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|password|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]

PROHIBITED_ARTIFACT_SUFFIXES = {
    ".pkl",
    ".pickle",
    ".joblib",
    ".parquet",
    ".feather",
    ".rds",
    ".rda",
    ".sqlite",
    ".sqlite3",
    ".db",
}

REQUIRED_SYNTHETIC_MODULES = [
    "src/ml_product/synthetic_data/__init__.py",
    "src/ml_product/synthetic_data/config.py",
    "src/ml_product/synthetic_data/generator.py",
    "src/ml_product/synthetic_data/patients.py",
    "src/ml_product/synthetic_data/admissions.py",
    "src/ml_product/synthetic_data/diagnoses.py",
    "src/ml_product/synthetic_data/ward_capacity.py",
    "src/ml_product/synthetic_data/workforce.py",
    "src/ml_product/synthetic_data/outcomes.py",
    "src/ml_product/synthetic_data/quality_injection.py",
    "src/ml_product/synthetic_data/validation.py",
    "src/ml_product/synthetic_data/metadata.py",
    "src/ml_product/synthetic_data/writers.py",
]

SAMPLE_DATASETS = [
    "patients",
    "admissions",
    "diagnoses",
    "ward_capacity",
    "workforce",
    "outcomes",
]

SAMPLE_METADATA_FILES = [
    "data/sample/generation_manifest.json",
    "data/sample/data_quality_issues.json",
    "data/sample/dataset_summary.json",
]

REQUIRED_DATABASE_MODULES = [
    "src/ml_product/ingestion/config.py",
    "src/ml_product/ingestion/database.py",
    "src/ml_product/ingestion/loader.py",
    "src/ml_product/ingestion/manifest.py",
    "src/ml_product/ingestion/lineage.py",
    "src/ml_product/ingestion/build.py",
    "src/ml_product/ingestion/logical_view_client.py",
    "src/ml_product/ingestion/local_view_client.py",
    "src/ml_product/ingestion/denodo_client.py",
    "src/ml_product/validation/data_contracts.py",
    "src/ml_product/validation/database_checks.py",
    "src/ml_product/validation/quality_checks.py",
    "src/ml_product/validation/reconciliation.py",
    "src/ml_product/linking/deterministic_linker.py",
    "src/ml_product/linking/duplicate_detector.py",
    "src/ml_product/linking/linkage_quality.py",
]

REQUIRED_DATABASE_SQL = [
    "database/schema/001_create_schemas.sql",
    "database/schema/010_create_raw_tables.sql",
    "database/schema/020_create_staged_tables.sql",
    "database/schema/030_create_quality_tables.sql",
    "database/schema/040_create_metadata_tables.sql",
    "database/views/100_patient_admission_view.sql",
    "database/views/110_admission_diagnosis_summary.sql",
    "database/views/120_daily_ward_operational_context.sql",
    "database/views/130_admission_operational_context.sql",
    "database/views/140_outcome_context_view.sql",
    "database/views/150_model_source_view.sql",
    "database/validation/200_primary_key_checks.sql",
    "database/validation/210_foreign_key_checks.sql",
    "database/validation/220_domain_checks.sql",
    "database/validation/230_temporal_checks.sql",
    "database/validation/240_quality_fixture_reconciliation.sql",
    "database/validation/250_curated_view_checks.sql",
    "database/seeds/controlled_vocabularies.sql",
]

DATABASE_EVIDENCE_FILES = [
    "reports/data_quality/database_build_manifest.json",
    "reports/data_quality/database_validation.json",
    "reports/data_quality/linkage_quality.json",
    "reports/data_quality/curated_view_summary.json",
    "reports/data_quality/database_build_report.md",
]

REQUIRED_FEATURE_MODULES = [
    "src/ml_product/features/__init__.py",
    "src/ml_product/features/config.py",
    "src/ml_product/features/source.py",
    "src/ml_product/features/eligibility.py",
    "src/ml_product/features/temporal.py",
    "src/ml_product/features/builder.py",
    "src/ml_product/features/transformers.py",
    "src/ml_product/features/leakage.py",
    "src/ml_product/features/splitting.py",
    "src/ml_product/features/registry.py",
    "src/ml_product/features/validation.py",
    "src/ml_product/features/metadata.py",
    "src/ml_product/features/writers.py",
]

FEATURE_EVIDENCE_FILES = [
    "reports/model_evaluation/feature_build_manifest.json",
    "reports/model_evaluation/feature_registry.json",
    "reports/model_evaluation/split_summary.json",
    "reports/model_evaluation/exclusion_summary.json",
    "reports/model_evaluation/leakage_report.json",
    "reports/model_evaluation/preprocessor_metadata.json",
    "reports/model_evaluation/feature_build_report.md",
]

REQUIRED_MODELLING_MODULES = [
    "src/ml_product/modelling/__init__.py",
    "src/ml_product/modelling/config.py",
    "src/ml_product/modelling/data.py",
    "src/ml_product/modelling/baselines.py",
    "src/ml_product/modelling/logistic_regression.py",
    "src/ml_product/modelling/random_forest.py",
    "src/ml_product/modelling/xgboost_model.py",
    "src/ml_product/modelling/training.py",
    "src/ml_product/modelling/prediction.py",
    "src/ml_product/modelling/evaluation.py",
    "src/ml_product/modelling/thresholding.py",
    "src/ml_product/modelling/calibration.py",
    "src/ml_product/modelling/explainability.py",
    "src/ml_product/modelling/fairness.py",
    "src/ml_product/modelling/comparison.py",
    "src/ml_product/modelling/selection.py",
    "src/ml_product/modelling/metadata.py",
    "src/ml_product/modelling/reporting.py",
    "src/ml_product/modelling/validation.py",
    "src/ml_product/modelling/writers.py",
]

MODEL_EVIDENCE_FILES = [
    "reports/model_evaluation/model_training_manifest.json",
    "reports/model_evaluation/baseline_metrics.json",
    "reports/model_evaluation/validation_metrics.json",
    "reports/model_evaluation/test_metrics.json",
    "reports/model_evaluation/model_comparison.json",
    "reports/model_evaluation/threshold_analysis.json",
    "reports/model_evaluation/calibration_report.json",
    "reports/model_evaluation/feature_importance.json",
    "reports/model_evaluation/local_explanations.json",
    "reports/model_evaluation/fairness_report.json",
    "reports/model_evaluation/candidate_recommendation.json",
    "reports/model_evaluation/model_evaluation_report.md",
    "reports/model_evaluation/model_card.md",
]

REQUIRED_REGISTRY_MODULES = [
    "src/ml_product/registry/__init__.py",
    "src/ml_product/registry/config.py",
    "src/ml_product/registry/models.py",
    "src/ml_product/registry/storage.py",
    "src/ml_product/registry/registry.py",
    "src/ml_product/registry/registration.py",
    "src/ml_product/registry/governance.py",
    "src/ml_product/registry/approval.py",
    "src/ml_product/registry/activation.py",
    "src/ml_product/registry/rollback.py",
    "src/ml_product/registry/compatibility.py",
    "src/ml_product/registry/audit.py",
    "src/ml_product/registry/metadata.py",
    "src/ml_product/registry/validation.py",
    "src/ml_product/registry/writers.py",
]

REQUIRED_SERVING_MODULES = [
    "src/ml_product/serving/__init__.py",
    "src/ml_product/serving/config.py",
    "src/ml_product/serving/app.py",
    "src/ml_product/serving/dependencies.py",
    "src/ml_product/serving/loader.py",
    "src/ml_product/serving/schemas.py",
    "src/ml_product/serving/preprocessing.py",
    "src/ml_product/serving/predictor.py",
    "src/ml_product/serving/risk_bands.py",
    "src/ml_product/serving/explanations.py",
    "src/ml_product/serving/authentication.py",
    "src/ml_product/serving/logging.py",
    "src/ml_product/serving/health.py",
    "src/ml_product/serving/metadata.py",
    "src/ml_product/serving/errors.py",
    "src/ml_product/serving/validation.py",
]

REGISTRY_EVIDENCE_FILES = [
    "reports/model_evaluation/model_registry_manifest.json",
    "reports/model_evaluation/registry_validation.json",
    "reports/model_evaluation/governance_review.json",
    "reports/model_evaluation/approval_decision.json",
    "reports/model_evaluation/activation_status.json",
    "reports/model_evaluation/serving_contract.json",
    "reports/model_evaluation/serving_readiness.json",
    "reports/model_evaluation/registry_audit_summary.json",
    "reports/model_evaluation/model_serving_report.md",
]

REQUIRED_RSHINY_FILES = [
    "rshiny/app.R",
    "rshiny/global.R",
    "rshiny/config.R",
    "rshiny/R/api_client.R",
    "rshiny/R/app_config.R",
    "rshiny/R/validation.R",
    "rshiny/R/prediction_contract.R",
    "rshiny/R/batch_contract.R",
    "rshiny/R/batch_validation.R",
    "rshiny/R/batch_presenter.R",
    "rshiny/R/export_utils.R",
    "rshiny/R/evidence_client.R",
    "rshiny/R/performance_presenter.R",
    "rshiny/R/governance_presenter.R",
    "rshiny/R/monitoring_client.R",
    "rshiny/R/monitoring_validation.R",
    "rshiny/R/monitoring_presenter.R",
    "rshiny/R/retraining_client.R",
    "rshiny/R/retraining_validation.R",
    "rshiny/R/retraining_presenter.R",
    "rshiny/R/prediction_presenter.R",
    "rshiny/R/review_mode.R",
    "rshiny/R/error_handling.R",
    "rshiny/R/accessibility.R",
    "rshiny/R/utils.R",
    "rshiny/modules/mod_overview.R",
    "rshiny/modules/mod_prediction.R",
    "rshiny/modules/mod_batch_scoring.R",
    "rshiny/modules/mod_performance.R",
    "rshiny/modules/mod_monitoring.R",
    "rshiny/modules/mod_retraining_review.R",
    "rshiny/modules/mod_governance.R",
    "rshiny/modules/mod_feedback.R",
    "rshiny/modules/mod_status_banner.R",
    "rshiny/tests/testthat/test-config.R",
    "rshiny/tests/testthat/test-contract.R",
    "rshiny/tests/testthat/test-api-client.R",
    "rshiny/tests/testthat/test-batch-contract.R",
    "rshiny/tests/testthat/test-evidence.R",
    "rshiny/tests/testthat/test-exports.R",
    "rshiny/tests/testthat/test-feedback.R",
    "rshiny/tests/testthat/test-monitoring.R",
    "rshiny/tests/testthat/test-retraining.R",
    "rshiny/tests/testthat/test-review-mode.R",
    "rshiny/www/app.css",
    "rshiny/www/sample_cohort_template.csv",
    "rshiny/README.md",
]

RSHINY_EVIDENCE_FILES = [
    "reports/uat/rshiny_mvp_manifest.json",
    "reports/uat/rshiny_api_contract_validation.json",
    "reports/uat/rshiny_test_summary.json",
    "reports/uat/rshiny_accessibility_check.json",
    "reports/uat/rshiny_review_mode_evidence.json",
    "reports/uat/rshiny_feedback_contract.json",
    "reports/uat/rshiny_mvp_report.md",
    "reports/uat/rshiny_advanced_manifest.json",
    "reports/uat/rshiny_batch_contract.json",
    "reports/uat/rshiny_batch_test_summary.json",
    "reports/uat/rshiny_performance_contract.json",
    "reports/uat/rshiny_governance_contract.json",
    "reports/uat/rshiny_export_contract.json",
    "reports/uat/rshiny_browser_test_summary.json",
    "reports/uat/rshiny_accessibility_advanced_check.json",
    "reports/uat/rshiny_advanced_report.md",
    "reports/uat/rshiny_monitoring_contract.json",
    "reports/uat/rshiny_monitoring_test_summary.json",
    "reports/uat/rshiny_monitoring_accessibility.json",
    "reports/uat/rshiny_monitoring_report.md",
    "reports/uat/rshiny_retraining_contract.json",
    "reports/uat/rshiny_retraining_test_summary.json",
    "reports/uat/rshiny_retraining_accessibility.json",
    "reports/uat/rshiny_retraining_report.md",
]

REQUIRED_RETRAINING_MODULES = [
    "src/ml_product/retraining/__init__.py",
    "src/ml_product/retraining/config.py",
    "src/ml_product/retraining/pipeline.py",
    "src/ml_product/retraining/eligibility.py",
    "src/ml_product/retraining/dataset.py",
    "src/ml_product/retraining/splitting.py",
    "src/ml_product/retraining/preprocessing.py",
    "src/ml_product/retraining/training.py",
    "src/ml_product/retraining/evaluation.py",
    "src/ml_product/retraining/champion.py",
    "src/ml_product/retraining/challenger.py",
    "src/ml_product/retraining/comparison.py",
    "src/ml_product/retraining/calibration.py",
    "src/ml_product/retraining/fairness.py",
    "src/ml_product/retraining/stability.py",
    "src/ml_product/retraining/gates.py",
    "src/ml_product/retraining/recommendation.py",
    "src/ml_product/retraining/registration.py",
    "src/ml_product/retraining/audit.py",
    "src/ml_product/retraining/metadata.py",
    "src/ml_product/retraining/reports.py",
    "src/ml_product/retraining/validation.py",
    "src/ml_product/retraining/writers.py",
]

RETRAINING_EVIDENCE_FILES = [
    "reports/retraining/retraining_eligibility.json",
    "reports/retraining/retraining_dataset_manifest.json",
    "reports/retraining/retraining_split_summary.json",
    "reports/retraining/retraining_preprocessor_metadata.json",
    "reports/retraining/challenger_training_manifest.json",
    "reports/retraining/champion_metrics.json",
    "reports/retraining/challenger_metrics.json",
    "reports/retraining/champion_challenger_comparison.json",
    "reports/retraining/challenger_calibration.json",
    "reports/retraining/challenger_threshold_analysis.json",
    "reports/retraining/retraining_fairness_report.json",
    "reports/retraining/retraining_stability_report.json",
    "reports/retraining/promotion_gates.json",
    "reports/retraining/retraining_recommendation.json",
    "reports/retraining/retraining_audit_summary.json",
    "reports/retraining/retraining_report.md",
]

REQUIRED_RELEASE_MODULES = [
    "src/ml_product/release/__init__.py",
    "src/ml_product/release/config.py",
    "src/ml_product/release/versioning.py",
    "src/ml_product/release/inventory.py",
    "src/ml_product/release/governance.py",
    "src/ml_product/release/security.py",
    "src/ml_product/release/containers.py",
    "src/ml_product/release/readiness.py",
    "src/ml_product/release/manifest.py",
    "src/ml_product/release/validation.py",
    "src/ml_product/release/reporting.py",
    "src/ml_product/release/writers.py",
]

RELEASE_EVIDENCE_FILES = [
    "reports/assurance/release_manifest.json",
    "reports/assurance/release_readiness.json",
    "reports/assurance/release_gates.json",
    "reports/assurance/container_build_manifest.json",
    "reports/assurance/container_validation.json",
    "reports/assurance/local_deployment_smoke.json",
    "reports/assurance/security_scan_summary.json",
    "reports/assurance/dependency_assurance.json",
    "reports/assurance/python_dependency_summary.json",
    "reports/assurance/r_dependency_summary.json",
    "reports/assurance/sbom_manifest.json",
    "reports/assurance/workflow_inventory.json",
    "reports/assurance/ci_local_validation.json",
    "reports/assurance/release_assurance_report.md",
]

PORTFOLIO_EVIDENCE_FILES = [
    "reports/portfolio/milestone_audit.json",
    "reports/portfolio/milestone_audit.md",
    "reports/portfolio/evidence_integrity.json",
    "reports/portfolio/final_test_summary.json",
    "reports/portfolio/final_test_summary.md",
    "reports/portfolio/coverage_summary.json",
    "reports/portfolio/repository_inventory.json",
    "reports/portfolio/initial_commit_inventory.json",
    "reports/portfolio/portfolio_readiness.json",
    "reports/portfolio/portfolio_readiness.md",
    "reports/assurance/final_security_review.json",
    "reports/assurance/final_security_review.md",
    "reports/assurance/remote_ci_validation.json",
    "reports/assurance/remote_ci_validation.md",
]

PORTFOLIO_DOCS = [
    "docs/portfolio_case_study.md",
    "docs/interview_model_answer.md",
    "docs/interview_questions_and_answers.md",
    "docs/architecture_overview.md",
    "docs/end_to_end_data_flow.md",
    "docs/end_to_end_model_flow.md",
    "docs/end_to_end_serving_flow.md",
    "docs/end_to_end_governance_flow.md",
    "docs/end_to_end_delivery_flow.md",
    "docs/portfolio_screenshot_runbook.md",
    "docs/milestones/milestone-14.md",
]

PORTFOLIO_ADRS = [
    "docs/adr/0065-first-commit-occurs-only-after-full-local-assurance.md",
    "docs/adr/0066-remote-ci-evidence-must-be-genuine.md",
    "docs/adr/0067-portfolio-readiness-is-distinct-from-operational-release.md",
    "docs/adr/0068-external-commercial-blockers-do-not-justify-fabricated-evidence.md",
    "docs/adr/0069-weak-model-evidence-remains-visible-in-final-portfolio.md",
    "docs/adr/0070-initial-release-does-not-approve-or-activate-model.md",
]

PORTFOLIO_DIAGRAMS = [
    "docs/diagrams/system-context.mmd",
    "docs/diagrams/data-architecture.mmd",
    "docs/diagrams/model-lifecycle.mmd",
    "docs/diagrams/serving-architecture.mmd",
    "docs/diagrams/governance-workflow.mmd",
    "docs/diagrams/monitoring-retraining-loop.mmd",
    "docs/diagrams/cicd-release-flow.mmd",
]

INTERVIEW_DOCS = [
    "docs/interview_architecture.md",
    "docs/end_to_end_lineage.md",
    "docs/interview_evidence_index.md",
    "docs/interview_demo_guide.md",
    "docs/interview_talking_points.md",
    "docs/interview_star_narrative.md",
    "docs/portfolio_capability_map.md",
    "docs/lifecycle_orchestration_demo.md",
]

INTERVIEW_DIAGRAMS = [
    "docs/diagrams/interview-architecture.mmd",
]

CAPABILITY_STATUS_VOCABULARY = {
    "implemented_and_tested",
    "live_validated",
    "offline_mock_validated",
    "documented_extension",
    "requires_external_environment",
}

REQUIRED_WORKFLOWS = [
    ".github/workflows/quality.yml",
    ".github/workflows/python-tests.yml",
    ".github/workflows/r-tests.yml",
    ".github/workflows/integration-tests.yml",
    ".github/workflows/security.yml",
    ".github/workflows/container.yml",
    ".github/workflows/release-assurance.yml",
]

REQUIRED_MONITORING_MODULES = [
    "src/ml_product/monitoring/__init__.py",
    "src/ml_product/monitoring/config.py",
    "src/ml_product/monitoring/pipeline.py",
    "src/ml_product/monitoring/baseline.py",
    "src/ml_product/monitoring/windows.py",
    "src/ml_product/monitoring/schema.py",
    "src/ml_product/monitoring/data_quality.py",
    "src/ml_product/monitoring/numeric_drift.py",
    "src/ml_product/monitoring/categorical_drift.py",
    "src/ml_product/monitoring/missingness.py",
    "src/ml_product/monitoring/prediction_drift.py",
    "src/ml_product/monitoring/performance.py",
    "src/ml_product/monitoring/calibration.py",
    "src/ml_product/monitoring/operational.py",
    "src/ml_product/monitoring/alerts.py",
    "src/ml_product/monitoring/review.py",
    "src/ml_product/monitoring/metadata.py",
    "src/ml_product/monitoring/reports.py",
    "src/ml_product/monitoring/validation.py",
    "src/ml_product/monitoring/writers.py",
]

MONITORING_EVIDENCE_FILES = [
    "reports/monitoring/monitoring_baseline_manifest.json",
    "reports/monitoring/monitoring_run_manifest.json",
    "reports/monitoring/schema_monitoring.json",
    "reports/monitoring/data_quality_monitoring.json",
    "reports/monitoring/numeric_drift.json",
    "reports/monitoring/categorical_drift.json",
    "reports/monitoring/missingness_drift.json",
    "reports/monitoring/prediction_drift.json",
    "reports/monitoring/performance_monitoring.json",
    "reports/monitoring/calibration_monitoring.json",
    "reports/monitoring/operational_monitoring.json",
    "reports/monitoring/monitoring_alerts.json",
    "reports/monitoring/monitoring_review.json",
    "reports/monitoring/monitoring_summary.json",
    "reports/monitoring/monitoring_scenario_summary.json",
    "reports/monitoring/monitoring_report.md",
]

PROHIBITED_PREDICTORS = {
    "discharge_datetime",
    "length_of_stay_days_source",
    "length_of_stay_days_governed",
    "long_stay_flag_source",
    "long_stay_flag_governed",
    "readmission_30d",
    "discharge_destination",
    "outcome_quality_status",
    "admission_id",
    "patient_id",
}


def _existing_files() -> Iterable[Path]:
    ignored_parts = {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "htmlcov",
        "renv",
    }
    for path in ROOT.rglob("*"):
        if path.is_file() and not ignored_parts.intersection(path.relative_to(ROOT).parts):
            yield path


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            document = yaml.safe_load(handle)
    except yaml.YAMLError as exc:
        raise ValueError(f"{path.relative_to(ROOT)} is not valid YAML: {exc}") from exc
    if not isinstance(document, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain a YAML mapping.")
    return document


def validate_structure() -> list[str]:
    errors: list[str] = []
    for file_name in REQUIRED_ROOT_FILES:
        if not (ROOT / file_name).is_file():
            errors.append(f"Missing required root file: {file_name}")
    for directory in REQUIRED_DIRECTORIES:
        if not (ROOT / directory).is_dir():
            errors.append(f"Missing required directory: {directory}")
    return errors


def validate_docs() -> list[str]:
    errors: list[str] = []
    for doc in [*REQUIRED_DOCS, *INTERVIEW_DOCS]:
        path = ROOT / doc
        if not path.is_file():
            errors.append(f"Missing required documentation: {doc}")
            continue
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) < 200:
            errors.append(f"Documentation is too thin for Milestone 1: {doc}")
    for diagram in INTERVIEW_DIAGRAMS:
        path = ROOT / diagram
        if not path.is_file():
            errors.append(f"Missing required architecture diagram source: {diagram}")
            continue
        text = path.read_text(encoding="utf-8")
        if "flowchart" not in text or "DataPlane" not in text or "ControlPlane" not in text:
            errors.append(f"Architecture diagram is not a readable Mermaid flowchart: {diagram}")
    errors.extend(_validate_interview_evidence_docs())
    return errors


def _validate_interview_evidence_docs() -> list[str]:
    errors: list[str] = []
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    evidence_index = (ROOT / "docs/interview_evidence_index.md").read_text(encoding="utf-8")
    architecture = (ROOT / "docs/interview_architecture.md").read_text(encoding="utf-8")
    demo = (ROOT / "docs/interview_demo_guide.md").read_text(encoding="utf-8")
    for status in CAPABILITY_STATUS_VOCABULARY:
        if status not in evidence_index:
            errors.append(f"Evidence index missing capability status: {status}")
    for phrase in [
        "Synthetic data",
        "PostgreSQL",
        "Denodo",
        "SAS Viya registration",
        "Promotion assessment",
        "Local activation",
        "Orchestration",
    ]:
        if phrase not in evidence_index:
            errors.append(f"Evidence index missing capability row: {phrase}")
    for phrase in [
        "fully synthetic",
        "External promotion never activates the local model",
        "live SAS Viya registration and promotion require",
    ]:
        if phrase not in architecture:
            errors.append(f"Interview architecture missing disclosure: {phrase}")
    if "external promotion is separate from local activation" not in demo:
        errors.append("Interview demo must disclose promotion versus activation boundary.")
    unsupported_claims = [
        "live SAS Viya validated",
        "live SAS Viya registration validated",
        "live SAS Viya promotion validated",
        "real clinical deployment",
        "real patient outcome",
    ]
    combined = "\n".join(
        [
            readme,
            evidence_index,
            architecture,
            demo,
            (ROOT / "docs/interview_talking_points.md").read_text(encoding="utf-8"),
            (ROOT / "docs/interview_star_narrative.md").read_text(encoding="utf-8"),
            (ROOT / "docs/portfolio_capability_map.md").read_text(encoding="utf-8"),
        ]
    )
    lowered = combined.lower()
    for claim in unsupported_claims:
        if claim.lower() in lowered:
            errors.append(f"Unsupported interview documentation claim: {claim}")
    for link in _markdown_links(readme):
        if link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = link.split("#", 1)[0]
        if target and not (ROOT / target).exists():
            errors.append(f"README link target does not exist: {link}")
    for path in _backtick_paths(evidence_index):
        if not (ROOT / path).exists():
            errors.append(f"Evidence index path does not exist: {path}")
    return errors


def _markdown_links(text: str) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)


def _backtick_paths(text: str) -> list[str]:
    paths: list[str] = []
    for value in re.findall(r"`([^`]+)`", text):
        if value.startswith(("make ", "python3 ", "curated.", "live_", "offline_", "implemented_")):
            continue
        if "/" not in value and "." not in Path(value).name:
            continue
        if any(part in value for part in ("*", " ", ",")):
            continue
        if value.startswith(("http://", "https://")):
            continue
        paths.append(value)
    return paths


def validate_config() -> list[str]:
    errors: list[str] = []
    for config in REQUIRED_CONFIGS:
        path = ROOT / config
        if not path.is_file():
            errors.append(f"Missing required config: {config}")
            continue
        try:
            document = _load_yaml(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        for key in ("version", "description", "implementation_status", "enabled"):
            if key not in document:
                errors.append(f"{config} missing required key: {key}")
        if "integration_modes" in document:
            modes = document["integration_modes"]
            if not isinstance(modes, dict):
                errors.append(f"{config} integration_modes must be a mapping.")
            else:
                for mode in modes.values():
                    if mode not in VALID_INTEGRATION_MODES:
                        errors.append(f"{config} has unsupported integration mode: {mode}")
    return errors


def validate_synthetic_data_foundation() -> list[str]:
    errors: list[str] = []
    for module in REQUIRED_SYNTHETIC_MODULES:
        if not (ROOT / module).is_file():
            errors.append(f"Missing synthetic-data module: {module}")
    for dataset in SAMPLE_DATASETS:
        for suffix in ("csv", "parquet"):
            path = ROOT / "data" / "sample" / f"{dataset}.{suffix}"
            if not path.is_file():
                errors.append(f"Missing committed sample file: {path.relative_to(ROOT)}")
            elif path.stat().st_size > 1_000_000:
                errors.append(
                    f"Sample file is too large for version control: {path.relative_to(ROOT)}"
                )
    for file_name in SAMPLE_METADATA_FILES:
        if not (ROOT / file_name).is_file():
            errors.append(f"Missing sample metadata file: {file_name}")
    raw_files = [
        path
        for path in (ROOT / "data" / "raw").glob("*")
        if path.is_file() and path.name != ".gitkeep"
    ]
    if raw_files:
        errors.append(
            "data/raw contains committed files; Milestone 2 sample outputs belong in data/sample"
        )
    dictionary = ROOT / "docs" / "data_dictionary.md"
    if dictionary.is_file():
        text = dictionary.read_text(encoding="utf-8")
        for dataset in SAMPLE_DATASETS:
            if f"## {dataset}" not in text:
                errors.append(f"Data dictionary missing dataset section: {dataset}")
    return errors


def validate_database_foundation() -> list[str]:
    errors: list[str] = []
    for module in REQUIRED_DATABASE_MODULES:
        if not (ROOT / module).is_file():
            errors.append(f"Missing database Python module: {module}")
    for sql_file in REQUIRED_DATABASE_SQL:
        path = ROOT / sql_file
        if not path.is_file():
            errors.append(f"Missing database SQL file: {sql_file}")
        elif (
            sql_file.startswith("database/views")
            and "select *" in path.read_text(encoding="utf-8").lower()
        ):
            errors.append(f"Governed view SQL must not use SELECT *: {sql_file}")
    for evidence in DATABASE_EVIDENCE_FILES:
        path = ROOT / evidence
        if not path.is_file():
            errors.append(f"Missing database evidence file: {evidence}")
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "/Users/" in text:
                errors.append(f"Database evidence contains an absolute user path: {evidence}")
    config = _load_yaml(ROOT / "config/database.yaml")
    provider = config.get("logical_layer", {}).get("provider")
    if provider != "denodo_compatible_local":
        errors.append("Database logical_layer.provider must be denodo_compatible_local")
    if any(path.name != ".gitkeep" for path in (ROOT / "denodo/evidence").glob("*")):
        errors.append("denodo/evidence must not contain fabricated Denodo evidence")
    return errors


def validate_boundaries() -> list[str]:
    errors: list[str] = []
    for path in _existing_files():
        relative = path.relative_to(ROOT)
        allowed_sample_parquet = (
            relative.parts[:2] == ("data", "sample") and path.suffix == ".parquet"
        )
        allowed_generated_database = (
            relative.parts[:2] == ("data", "processed") and path.suffix == ".duckdb"
        )
        allowed_generated_features = relative.parts[:3] == (
            "data",
            "processed",
            "features",
        ) and path.suffix in {".parquet", ".csv", ".json"}
        allowed_candidate_artifact = relative.parts[:2] == (
            "models",
            "candidate",
        ) and path.suffix in {".joblib", ".json"}
        allowed_registered_artifact = relative.parts[:2] == (
            "models",
            "registered",
        ) and path.suffix in {".joblib", ".json"}
        if (
            path.suffix.lower() in PROHIBITED_ARTIFACT_SUFFIXES
            and not allowed_sample_parquet
            and not allowed_generated_database
            and not allowed_generated_features
            and not allowed_candidate_artifact
            and not allowed_registered_artifact
        ):
            errors.append(
                f"Repository must not commit generated artefact outside allowed samples: {relative}"
            )
        if path.stat().st_size > 2_000_000 and not allowed_generated_database:
            errors.append(f"Unexpectedly large Milestone 1 file: {relative}")
        if path.suffix.lower() in {".md", ".py", ".yml", ".yaml", ".env", ".example", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    errors.append(f"Potential committed secret in {relative}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "Denodo: live_validated" not in readme:
        errors.append("README must describe current Denodo live-validation status.")
    if "Live SAS Viya registration and promotion: requires_external_environment" not in readme:
        errors.append("README must describe live SAS Viya external-environment boundary.")
    if "Milestone 2" not in readme or "synthetic source" not in readme.lower():
        errors.append("README must describe Milestone 2 synthetic source-system status.")
    if "Milestone 3" not in readme or "DuckDB" not in readme:
        errors.append("README must describe Milestone 3 DuckDB logical-layer status.")
    if "Milestone 5" not in readme or "Feature" not in readme:
        errors.append("README must describe Milestone 5 feature-engineering status.")
    if "Milestone 6" not in readme or "model" not in readme.lower():
        errors.append("README must describe Milestone 6 model-development status.")
    return errors


def validate_feature_foundation() -> list[str]:
    errors: list[str] = []
    for module in REQUIRED_FEATURE_MODULES:
        if not (ROOT / module).is_file():
            errors.append(f"Missing feature module: {module}")
    config = _load_yaml(ROOT / "config/features.yaml")
    if config.get("implementation_status") != "implemented":
        errors.append("config/features.yaml must mark Milestone 5 as implemented.")
    if config.get("source", {}).get("view") != "curated.model_source_view":
        errors.append("Feature source must be curated.model_source_view.")
    if config.get("source", {}).get("provider") != "denodo_compatible_local":
        errors.append("Feature source provider must remain denodo_compatible_local.")
    predictors: list[str] = []
    for key in ("numeric", "categorical", "boolean"):
        predictors.extend(config.get("features", {}).get(key, []))
    prohibited = sorted(PROHIBITED_PREDICTORS.intersection(predictors))
    if prohibited:
        errors.append(f"Feature config includes prohibited predictors: {prohibited}")
    for evidence in FEATURE_EVIDENCE_FILES:
        path = ROOT / evidence
        if not path.is_file():
            errors.append(f"Missing feature evidence file: {evidence}")
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "/Users/" in text:
                errors.append(f"Feature evidence contains an absolute user path: {evidence}")
    leakage_path = ROOT / "reports/model_evaluation/leakage_report.json"
    if leakage_path.is_file():
        leakage = _load_json(leakage_path)
        if leakage.get("total_violations") != 0:
            errors.append("Feature leakage report must contain zero violations.")
    split_path = ROOT / "reports/model_evaluation/split_summary.json"
    if split_path.is_file():
        split = _load_json(split_path)
        if split.get("patient_overlap_count") != 0:
            errors.append("Split summary must contain zero patient overlap.")
        if split.get("admission_overlap_count") != 0:
            errors.append("Split summary must contain zero admission overlap.")
    registry_path = ROOT / "reports/model_evaluation/feature_registry.json"
    if registry_path.is_file():
        registry = _load_json(registry_path)
        if not registry.get("coverage_valid"):
            errors.append("Feature registry must cover every transformed feature.")
        if registry.get("registry_entry_count") != registry.get("output_feature_count"):
            errors.append("Feature registry count must match output feature count.")
    milestone_04 = ROOT / "docs/milestones/milestone-04.md"
    if milestone_04.is_file():
        text = milestone_04.read_text(encoding="utf-8")
        if "Externally blocked" not in text or "genuine access was unavailable" not in text:
            errors.append("Milestone 4 document must record genuine Denodo access as blocked.")
    if any(path.name != ".gitkeep" for path in (ROOT / "denodo/evidence").glob("*")):
        errors.append("denodo/evidence must not contain fabricated Denodo evidence")
    return errors


def validate_model_foundation() -> list[str]:
    errors: list[str] = []
    for module in REQUIRED_MODELLING_MODULES:
        if not (ROOT / module).is_file():
            errors.append(f"Missing modelling module: {module}")
    training_config = _load_yaml(ROOT / "config/model_training.yaml")
    threshold_config = _load_yaml(ROOT / "config/model_thresholds.yaml")
    if training_config.get("implementation_status") != "implemented":
        errors.append("config/model_training.yaml must mark Milestone 6 as implemented.")
    if threshold_config.get("implementation_status") != "implemented":
        errors.append("config/model_thresholds.yaml must mark thresholds as implemented.")
    if training_config.get("feature_source", {}).get("expected_feature_count") != 71:
        errors.append("Model training config must expect 71 transformed features.")
    for evidence in MODEL_EVIDENCE_FILES:
        path = ROOT / evidence
        if not path.is_file():
            errors.append(f"Missing model evidence file: {evidence}")
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "/Users/" in text:
                errors.append(f"Model evidence contains an absolute user path: {evidence}")
    manifest_path = ROOT / "reports/model_evaluation/model_training_manifest.json"
    recommendation_path = ROOT / "reports/model_evaluation/candidate_recommendation.json"
    calibration_path = ROOT / "reports/model_evaluation/calibration_report.json"
    comparison_path = ROOT / "reports/model_evaluation/model_comparison.json"
    importance_path = ROOT / "reports/model_evaluation/feature_importance.json"
    model_card_path = ROOT / "reports/model_evaluation/model_card.md"
    if manifest_path.is_file():
        manifest = _load_json(manifest_path)
        feature_manifest = _load_json(ROOT / "reports/model_evaluation/feature_build_manifest.json")
        if manifest.get("feature_build_identifier") != feature_manifest.get(
            "feature_build_identifier"
        ):
            errors.append("Model manifest feature build identifier must match feature manifest.")
        if manifest.get("test_set_used_for_selection") is not False:
            errors.append("Model manifest must record test_set_used_for_selection=false.")
        if manifest.get("feature_count") != 71:
            errors.append("Model manifest must record 71 features.")
        xgboost_status = manifest.get("candidate_training_status", {}).get("xgboost", {})
        if xgboost_status.get("training_status") != "fitted":
            errors.append("XGBoost training status must be fitted for Milestone 6 completion.")
        if xgboost_status.get("fit_status") != "fitted":
            errors.append("XGBoost fit status must be fitted for Milestone 6 completion.")
        if xgboost_status.get("artifact_location") != "models/candidate/xgboost.json":
            errors.append("XGBoost artefact must be recorded as models/candidate/xgboost.json.")
        if not (ROOT / "models/candidate/xgboost.json").is_file():
            errors.append("Missing ignored local XGBoost candidate artefact.")
    if recommendation_path.is_file():
        recommendation = _load_json(recommendation_path)
        if recommendation.get("test_set_used_for_selection") is not False:
            errors.append("Recommendation must record test_set_used_for_selection=false.")
        if recommendation.get("approval_status") != "not_granted":
            errors.append("Recommendation must not grant approval.")
        if recommendation.get("deployment_status") != "not_performed":
            errors.append("Recommendation must not perform deployment.")
    if calibration_path.is_file():
        calibration = _load_json(calibration_path)
        isotonic = calibration.get("method_eligibility", {}).get("isotonic", {})
        if isotonic.get("eligible") is True:
            errors.append("Isotonic calibration must be blocked for the small validation set.")
    if comparison_path.is_file():
        comparison = _load_json(comparison_path)
        comparison_families = {row.get("model_family") for row in comparison.get("rows", [])}
        if "xgboost" not in comparison_families:
            errors.append("Model comparison must include XGBoost validation metrics.")
    if importance_path.is_file():
        importance = _load_json(importance_path)
        xgboost_importance = importance.get("candidate_global_importance", {}).get("xgboost")
        if not xgboost_importance or not xgboost_importance.get("permutation_importance"):
            errors.append("XGBoost permutation importance must be present.")
        if not xgboost_importance or not xgboost_importance.get("native_importance"):
            errors.append("XGBoost native importance must be present.")
    if model_card_path.is_file():
        card = model_card_path.read_text(encoding="utf-8")
        for status in (
            "R-Shiny integration: implemented locally",
            "Production approval: not granted",
            "Deployment: not performed",
        ):
            if status not in card:
                errors.append(f"Model card missing status: {status}")
    if any(path.name != ".gitkeep" for path in (ROOT / "models/approved").glob("*")):
        errors.append("models/approved must not contain Milestone 6 artefacts.")
    if any(path.name != ".gitkeep" for path in (ROOT / "sas_viya/model_evidence").glob("*")):
        errors.append("sas_viya/model_evidence must not contain fabricated evidence.")
    return errors


def validate_registry_foundation() -> list[str]:
    errors: list[str] = []
    for module in REQUIRED_REGISTRY_MODULES + REQUIRED_SERVING_MODULES:
        if not (ROOT / module).is_file():
            errors.append(f"Missing registry/serving module: {module}")
    registry_config = _load_yaml(ROOT / "config/model_registry.yaml")
    governance_config = _load_yaml(ROOT / "config/model_governance.yaml")
    serving_config = _load_yaml(ROOT / "config/serving.yaml")
    if registry_config.get("approval", {}).get("automatic_approval") is not False:
        errors.append("Automatic registry approval must be disabled.")
    if registry_config.get("activation", {}).get("require_approved_status") is not True:
        errors.append("Registry activation must require approved status.")
    if governance_config.get("approval", {}).get("automatic") is not False:
        errors.append("Governance approval must not be automatic.")
    if (
        serving_config.get("model", {}).get("allow_registered_candidate_for_local_review")
        is not False
    ):
        errors.append("Serving review mode must be disabled by default.")
    if serving_config.get("service", {}).get("environment") != "local":
        errors.append("Committed serving config must be local.")
    for evidence in REGISTRY_EVIDENCE_FILES:
        path = ROOT / evidence
        if not path.is_file():
            errors.append(f"Missing registry evidence file: {evidence}")
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "/Users/" in text:
                errors.append(f"Registry evidence contains an absolute user path: {evidence}")
    registry_path = ROOT / "models/registry.json"
    if not registry_path.is_file():
        errors.append("Missing models/registry.json metadata.")
    else:
        registry = _load_json(registry_path)
        if registry.get("active_model") is not None:
            errors.append("Real registry must not have an active model without explicit approval.")
        versions = [
            version for entry in registry.get("models", []) for version in entry.get("versions", [])
        ]
        if not versions:
            errors.append("Registry must contain the registered Milestone 6 candidate.")
        for version in versions:
            if version.get("status") not in {
                "registered",
                "approval_pending",
                "approved",
                "active",
                "rejected",
                "retired",
                "archived",
            }:
                errors.append("Registry contains unsupported status.")
            if version.get("candidate_identifier") == "CAND-85EA9202CAD6FE7F":
                if version.get("status") != "registered":
                    errors.append(
                        "Committed XGBoost candidate should remain registered, not active."
                    )
                if version.get("approval_decision") is not None:
                    errors.append(
                        "Committed XGBoost candidate must not have a granted approval decision."
                    )
    manifest_path = ROOT / "reports/model_evaluation/model_registry_manifest.json"
    readiness_path = ROOT / "reports/model_evaluation/serving_readiness.json"
    approval_path = ROOT / "reports/model_evaluation/approval_decision.json"
    if manifest_path.is_file():
        manifest = _load_json(manifest_path)
        if manifest.get("approval_state") != "pending":
            errors.append("Registry manifest must show pending approval.")
        if manifest.get("activation_state") != "inactive":
            errors.append("Registry manifest must show inactive activation state.")
    if readiness_path.is_file():
        readiness = _load_json(readiness_path)
        if readiness.get("production_deployment") is not False:
            errors.append("Serving readiness must not claim production deployment.")
        if readiness.get("approved_serving") is not False:
            errors.append("Approved serving must be false for the unapproved committed candidate.")
    if approval_path.is_file():
        approval = _load_json(approval_path)
        if approval.get("automatic_approval") is not False:
            errors.append("Approval evidence must show automatic approval is false.")
        if approval.get("decision") != "pending":
            errors.append("Committed approval decision must remain pending.")
    if not (ROOT / "infrastructure/docker/Dockerfile.api").is_file():
        errors.append("Missing local API Dockerfile foundation.")
    return errors


def validate_rshiny_foundation() -> list[str]:
    errors: list[str] = []
    for file_name in REQUIRED_RSHINY_FILES:
        if not (ROOT / file_name).is_file():
            errors.append(f"Missing R-Shiny file: {file_name}")
    for evidence in RSHINY_EVIDENCE_FILES:
        if not (ROOT / evidence).is_file():
            errors.append(f"Missing R-Shiny UAT evidence: {evidence}")
    config = _load_yaml(ROOT / "config/rshiny.yaml")
    features = config.get("features", {})
    if config.get("review_mode", {}).get("allow_ui_toggle") is not False:
        errors.append("R-Shiny review mode must not be toggleable from the UI.")
    for enabled in (
        "overview",
        "single_prediction",
        "cohort_scoring",
        "performance_dashboard",
        "model_governance",
        "monitoring",
        "feedback",
    ):
        if features.get(enabled) is not True:
            errors.append(f"R-Shiny Milestone 11 feature must be enabled: {enabled}")
    for disabled in (
        "drift_detection",
        "retraining",
        "governance_admin",
        "deployment_controls",
    ):
        if features.get(disabled) is not False:
            errors.append(f"R-Shiny mutation feature must remain disabled: {disabled}")
    cohort = config.get("cohort_scoring", {})
    if cohort.get("maximum_rows") != 100:
        errors.append("R-Shiny cohort maximum must match FastAPI batch maximum of 100.")
    if cohort.get("retain_uploads") is not False:
        errors.append("R-Shiny cohort uploads must not be retained.")
    if config.get("governance", {}).get("allow_state_changes") is not False:
        errors.append("R-Shiny governance page must be read-only.")
    executable_text = "\n".join(
        (ROOT / path).read_text(encoding="utf-8", errors="ignore")
        for path in (
            "rshiny/modules/mod_prediction.R",
            "rshiny/modules/mod_batch_scoring.R",
            "rshiny/modules/mod_performance.R",
            "rshiny/modules/mod_governance.R",
            "rshiny/modules/mod_monitoring.R",
            "rshiny/modules/mod_retraining_review.R",
            "rshiny/R/api_client.R",
        )
    )
    prohibited = [
        "reticulate::",
        "library(reticulate)",
        "DBI::",
        "duckdb::",
        "models/candidate",
        "models/registered",
        "patient_id",
        "admission_id",
        "long_stay_flag",
        "length_of_stay",
    ]
    for pattern in prohibited:
        if pattern in executable_text:
            errors.append(f"Prohibited R-Shiny implementation pattern: {pattern}")
    app_text = (ROOT / "rshiny/app.R").read_text(encoding="utf-8")
    if "Monitoring" not in app_text:
        errors.append("R-Shiny Monitoring page must be exposed for Milestone 11.")
    if "Retraining Review" not in app_text:
        errors.append("R-Shiny Retraining Review page must be exposed for Milestone 12.")
    for future_page in ("Drift",):
        if future_page in app_text:
            errors.append(f"R-Shiny future page must not be exposed: {future_page}")
    gov_text = (ROOT / "rshiny/modules/mod_governance.R").read_text(encoding="utf-8")
    for control in ("Approve", "Reject", "Activate", "Retire", "Roll back", "Register", "Deploy"):
        if control in gov_text:
            errors.append(f"R-Shiny governance mutation control must be absent: {control}")
    banner_text = (ROOT / "rshiny/modules/mod_status_banner.R").read_text(encoding="utf-8") + (
        ROOT / "rshiny/R/prediction_presenter.R"
    ).read_text(encoding="utf-8")
    for label in ("LOCAL REVIEW MODE", "SCORING UNAVAILABLE", "not approved"):
        if label not in banner_text:
            errors.append(f"Status banner missing required text: {label}")
    if any(path.name != ".gitkeep" for path in (ROOT / "sas_viya/model_evidence").glob("*")):
        errors.append("sas_viya/model_evidence must not contain fabricated SAS Viya evidence.")
    milestone_08 = (ROOT / "docs/milestones/milestone-08.md").read_text(encoding="utf-8")
    if "Externally blocked" not in milestone_08 or "genuine SAS Viya access" not in milestone_08:
        errors.append("Milestone 8 document must record SAS Viya as externally blocked.")
    milestone_09 = (ROOT / "docs/milestones/milestone-09.md").read_text(encoding="utf-8")
    if "Status: Complete" not in milestone_09:
        errors.append("Milestone 9 document must be complete after implementation.")
    milestone_10 = (ROOT / "docs/milestones/milestone-10.md").read_text(encoding="utf-8")
    if "Status: Complete" not in milestone_10:
        errors.append("Milestone 10 document must be complete after implementation.")
    browser_summary = _load_json(ROOT / "reports/uat/rshiny_browser_test_summary.json")
    if browser_summary.get("tests_skipped") != 0:
        errors.append("Milestone 10 browser-backed tests must not be skipped.")
    governance_contract = _load_json(ROOT / "reports/uat/rshiny_governance_contract.json")
    if not governance_contract.get("approval_pending"):
        errors.append("R-Shiny governance evidence must keep approval pending.")
    if not governance_contract.get("activation_inactive"):
        errors.append("R-Shiny governance evidence must keep activation inactive.")
    return errors


def validate_monitoring_foundation() -> list[str]:
    errors: list[str] = []
    for module in REQUIRED_MONITORING_MODULES:
        if not (ROOT / module).is_file():
            errors.append(f"Missing monitoring module: {module}")
    monitoring_config = _load_yaml(ROOT / "config/monitoring.yaml")
    thresholds = _load_yaml(ROOT / "config/drift_thresholds.yaml")
    if monitoring_config.get("implementation_status") != "implemented":
        errors.append("config/monitoring.yaml must mark monitoring as implemented.")
    if thresholds.get("implementation_status") != "implemented":
        errors.append("config/drift_thresholds.yaml must mark drift thresholds as implemented.")
    alerts_config = monitoring_config.get("alerts", {})
    if alerts_config.get("automatic_retraining") is not False:
        errors.append("Monitoring must not enable automatic retraining.")
    if alerts_config.get("automatic_model_replacement") is not False:
        errors.append("Monitoring must not enable automatic model replacement.")
    for evidence in MONITORING_EVIDENCE_FILES:
        path = ROOT / evidence
        if not path.is_file():
            errors.append(f"Missing monitoring evidence file: {evidence}")
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "/Users/" in text:
                errors.append(f"Monitoring evidence contains an absolute user path: {evidence}")
            for field in ("patient_id", "admission_id", "raw_inputs", "api_key"):
                if field in text:
                    errors.append(f"Monitoring evidence contains prohibited field text: {evidence}")
    review_path = ROOT / "reports/monitoring/monitoring_review.json"
    alerts_path = ROOT / "reports/monitoring/monitoring_alerts.json"
    summary_path = ROOT / "reports/monitoring/monitoring_summary.json"
    prediction_path = ROOT / "reports/monitoring/prediction_drift.json"
    performance_path = ROOT / "reports/monitoring/performance_monitoring.json"
    if review_path.is_file():
        review = _load_json(review_path)
        if review.get("retraining_status") != "not_implemented":
            errors.append("Monitoring review must not implement retraining.")
        if review.get("registry_mutation_status") != "none":
            errors.append("Monitoring review must not mutate the registry.")
        if review.get("model_replacement_status") != "none":
            errors.append("Monitoring review must not replace models.")
    if alerts_path.is_file():
        alerts = _load_json(alerts_path).get("alerts", [])
        if not alerts:
            errors.append("Monitoring representative run must include review alerts.")
        for alert in alerts:
            if alert.get("automatic_action") != "human_review_required":
                errors.append("Monitoring alerts may only require human review.")
    if summary_path.is_file():
        summary = _load_json(summary_path)
        if summary.get("automatic_action") != "none":
            errors.append("Monitoring summary automatic action must be none.")
    if prediction_path.is_file():
        prediction = _load_json(prediction_path)
        if prediction.get("performance_conclusion_available") is not False:
            errors.append("Prediction drift must not claim model performance degradation.")
        if "not performance drift" not in prediction.get("boundary_statement", ""):
            errors.append("Prediction drift evidence must include boundary statement.")
    if performance_path.is_file():
        performance = _load_json(performance_path)
        if performance.get("labels_available") is not True:
            errors.append("Performance monitoring must require outcome labels.")
        if performance.get("threshold_unchanged") is not True:
            errors.append("Monitoring must not change prediction threshold.")
        if performance.get("calibration_unchanged") is not True:
            errors.append("Monitoring must not change calibration.")
    source_text = "\n".join(
        (ROOT / path).read_text(encoding="utf-8", errors="ignore")
        for path in [
            "src/ml_product/monitoring/pipeline.py",
            "rshiny/modules/mod_monitoring.R",
        ]
    )
    for forbidden in ("fit(", "fit_transform(", "approve", "activate", "rollback"):
        if forbidden in source_text:
            errors.append(
                f"Monitoring implementation contains forbidden mutation token: {forbidden}"
            )
    if (ROOT / "data/monitoring/prediction_events.jsonl").exists():
        errors.append("Generated prediction event logs must not be committed in data/monitoring.")
    numbered_coverage = sorted(ROOT.glob(".coverage*"))
    if numbered_coverage:
        errors.append(f"Disposable coverage files must be removed: {numbered_coverage}")
    return errors


def validate_retraining_foundation() -> list[str]:
    errors: list[str] = []
    for module in REQUIRED_RETRAINING_MODULES:
        if not (ROOT / module).is_file():
            errors.append(f"Missing retraining module: {module}")
    retraining_config = _load_yaml(ROOT / "config/retraining.yaml")
    comparison_config = _load_yaml(ROOT / "config/champion_challenger.yaml")
    controls = retraining_config.get("controls", {})
    workflow = retraining_config.get("workflow", {})
    if workflow.get("automatic_execution") is not False:
        errors.append("Retraining automatic execution must be false.")
    for key in (
        "automatic_registration",
        "automatic_approval",
        "automatic_activation",
        "automatic_deployment",
    ):
        if controls.get(key) is not False:
            errors.append(f"Retraining control must be false: {key}")
    if (
        comparison_config.get("selection", {}).get("use_historical_test_set_for_selection")
        is not False
    ):
        errors.append("Champion-challenger selection must not use historical test set.")
    for evidence in RETRAINING_EVIDENCE_FILES:
        path = ROOT / evidence
        if not path.is_file():
            errors.append(f"Missing retraining evidence file: {evidence}")
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "/Users/" in text:
                errors.append(f"Retraining evidence contains an absolute user path: {evidence}")
            prohibited_fields = (
                "api_key_value",
                'raw_rows_logged": true',
                'patient_identifiers_logged": true',
            )
            for field in prohibited_fields:
                if field in text:
                    errors.append(f"Retraining evidence contains prohibited field text: {evidence}")
    recommendation_path = ROOT / "reports/retraining/retraining_recommendation.json"
    comparison_path = ROOT / "reports/retraining/champion_challenger_comparison.json"
    champion_path = ROOT / "reports/retraining/champion_metrics.json"
    gates_path = ROOT / "reports/retraining/promotion_gates.json"
    if recommendation_path.is_file():
        recommendation = _load_json(recommendation_path)
        if recommendation.get("approval_status") != "not_granted":
            errors.append("Retraining recommendation must not grant approval.")
        if recommendation.get("activation_status") != "inactive":
            errors.append("Retraining recommendation must not activate a model.")
        if recommendation.get("deployment_status") != "not_performed":
            errors.append("Retraining recommendation must not deploy a model.")
        if recommendation.get("automatic_action") != "none":
            errors.append("Retraining recommendation automatic action must be none.")
    if comparison_path.is_file():
        comparison = _load_json(comparison_path)
        if comparison.get("historical_test_set_used_for_selection") is not False:
            errors.append("Retraining comparison must not use historical test set.")
        if comparison.get("same_row_evaluation_confirmation") is not True:
            errors.append("Champion and challengers must use same-row evaluation.")
    if champion_path.is_file():
        champion = _load_json(champion_path)
        if champion.get("candidate_identifier") != "CAND-85EA9202CAD6FE7F":
            errors.append("Retraining champion must be the registered XGBoost candidate.")
        if (
            champion.get("approval_state") != "pending"
            or champion.get("activation_state") != "inactive"
        ):
            errors.append("Retraining champion must remain pending and inactive.")
    if gates_path.is_file():
        gates = _load_json(gates_path)
        if gates.get("approval_not_implied") is not True:
            errors.append("Promotion gates must state approval is not implied.")
    registry = _load_json(ROOT / "models/registry.json")
    if registry.get("active_model") is not None:
        errors.append("Retraining must not activate the real registry.")
    return errors


def validate_release_workflows() -> list[str]:
    errors: list[str] = []
    for workflow in REQUIRED_WORKFLOWS:
        path = ROOT / workflow
        if not path.is_file():
            errors.append(f"Missing release workflow: {workflow}")
            continue
        text = path.read_text(encoding="utf-8")
        payload = _load_yaml(path)
        if payload.get("permissions") != {"contents": "read"}:
            errors.append(f"Workflow must use contents: read permissions only: {workflow}")
        if "@main" in text or "@master" in text:
            errors.append(f"Workflow must not use floating action refs: {workflow}")
        if "write-all" in text:
            errors.append(f"Workflow must not use write-all permissions: {workflow}")
        prohibited = [
            "docker push",
            "gh release",
            "terraform apply",
            "az deployment",
            "aws cloudformation deploy",
            "kubectl apply",
            "activate-model",
            "record-approval-decision",
            "register-retraining-candidate",
        ]
        lowered = text.lower()
        for token in prohibited:
            if token in lowered:
                errors.append(
                    f"Workflow contains prohibited side-effect command {token}: {workflow}"
                )
        payload_any = cast(dict[Any, Any], payload)
        triggers = payload_any.get(True, payload.get("on", {}))
        if "pull_request" not in triggers and workflow != ".github/workflows/release-assurance.yml":
            errors.append(f"Pull request trigger missing: {workflow}")
    return errors


def validate_release_shell() -> list[str]:
    errors: list[str] = []
    script = ROOT / "scripts/smoke_test_local_deployment.sh"
    if not script.is_file():
        return ["Missing local deployment smoke script."]
    text = script.read_text(encoding="utf-8")
    for required in ["set -euo pipefail", "trap cleanup EXIT INT TERM", "docker compose"]:
        if required not in text:
            errors.append(f"Smoke script missing shell safety requirement: {required}")
    for prohibited in ["docker push", "terraform apply", "kubectl apply", "gh release"]:
        if prohibited in text.lower():
            errors.append(f"Smoke script contains prohibited command: {prohibited}")
    return errors


def validate_release_containers() -> list[str]:
    errors: list[str] = []
    api = ROOT / "infrastructure/docker/Dockerfile.api"
    rshiny = ROOT / "infrastructure/docker/Dockerfile.rshiny"
    compose = ROOT / "docker-compose.yml"
    review = ROOT / "docker-compose.review.yml"
    for path in [api, rshiny, compose, review]:
        if not path.is_file():
            errors.append(f"Missing container file: {path.relative_to(ROOT)}")
    if errors:
        return errors
    api_text = api.read_text(encoding="utf-8")
    rshiny_text = rshiny.read_text(encoding="utf-8")
    compose_text = compose.read_text(encoding="utf-8")
    review_text = review.read_text(encoding="utf-8")
    required_pairs = [
        ("API Dockerfile non-root user", "USER appuser", api_text),
        ("R-Shiny Dockerfile non-root user", "USER shiny", rshiny_text),
        ("API Dockerfile healthcheck", "HEALTHCHECK", api_text),
        ("R-Shiny Dockerfile healthcheck", "HEALTHCHECK", rshiny_text),
        ("API pinned base", "python:3.12.13-slim-trixie", api_text),
        ("R-Shiny pinned base", "r-base:4.4.2", rshiny_text),
        ("OCI revision label API", "org.opencontainers.image.revision", api_text),
        ("OCI revision label R-Shiny", "org.opencontainers.image.revision", rshiny_text),
        ("review override label", "local review only", review_text.lower()),
    ]
    for label, token, text in required_pairs:
        if token not in text:
            errors.append(f"Missing {label}: {token}")
    if "SERVING_REVIEW_MODE" in compose_text:
        errors.append("Base Compose must not enable review mode.")
    if "/var/run/docker.sock" in compose_text:
        errors.append("Compose must not mount Docker socket.")
    if "privileged" in compose_text.lower():
        errors.append("Compose must not enable privileged containers.")
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    for token in [
        ".git",
        ".coverage",
        "renv/library",
        "data/processed/*",
        "models/candidate/*",
        ".env",
    ]:
        if token not in dockerignore:
            errors.append(f".dockerignore missing exclusion: {token}")
    return errors


def validate_release_foundation() -> list[str]:
    errors: list[str] = []
    for module in REQUIRED_RELEASE_MODULES:
        if not (ROOT / module).is_file():
            errors.append(f"Missing release module: {module}")
    errors.extend(validate_release_workflows())
    errors.extend(validate_release_shell())
    errors.extend(validate_release_containers())
    config = _load_yaml(ROOT / "config/release.yaml")
    if config.get("artefacts", {}).get("publish_images") is not False:
        errors.append("Release config must disable image publication.")
    deployment = config.get("deployment", {})
    if (
        deployment.get("external_enabled") is not False
        or deployment.get("cloud_enabled") is not False
    ):
        errors.append("Release config must disable external and cloud deployment.")
    if deployment.get("require_manual_approval") is not True:
        errors.append("Release config must require manual approval.")
    for evidence in RELEASE_EVIDENCE_FILES:
        path = ROOT / evidence
        if not path.is_file():
            errors.append(f"Missing release assurance evidence: {evidence}")
        elif "/Users/" in path.read_text(encoding="utf-8", errors="ignore"):
            errors.append(f"Release evidence contains local absolute path: {evidence}")
    manifest = ROOT / "reports/assurance/release_manifest.json"
    readiness = ROOT / "reports/assurance/release_readiness.json"
    ci_local = ROOT / "reports/assurance/ci_local_validation.json"
    if manifest.is_file():
        payload = _load_json(manifest)
        if payload.get("remote_ci_executed") is not False:
            errors.append("Release manifest must report remote_ci_executed false.")
        revision = payload.get("git_revision")
        if not (
            revision == "uncommitted"
            or (
                isinstance(revision, str)
                and len(revision) == 40
                and set(revision) <= set("0123456789abcdef")
            )
        ):
            errors.append("Release manifest must report uncommitted or a genuine Git SHA.")
        if payload.get("publish_images") is not False:
            errors.append("Release manifest must report image publication false.")
    if readiness.is_file():
        payload = _load_json(readiness)
        if payload.get("local_review_readiness") != "ready_for_local_review":
            errors.append("Release readiness must be ready for local review.")
        if payload.get("operational_release_readiness") != "blocked_for_operational_release":
            errors.append("Operational release must be blocked.")
        if payload.get("model_approval_state") != "pending":
            errors.append("Release readiness must preserve pending approval.")
        if payload.get("model_activation_state") != "inactive":
            errors.append("Release readiness must preserve inactive activation.")
    if ci_local.is_file():
        payload = _load_json(ci_local)
        if payload.get("remote_ci_executed") is not False:
            errors.append("CI local validation must report remote CI false.")
        if payload.get("remote_run_ids") or payload.get("remote_workflow_urls"):
            errors.append("CI local validation must not fabricate remote run IDs or URLs.")
    return errors


def validate_portfolio_foundation() -> list[str]:
    errors: list[str] = []
    developer_path = "/Users/" + "privilege"
    for path_text in (
        PORTFOLIO_EVIDENCE_FILES + PORTFOLIO_DOCS + PORTFOLIO_ADRS + PORTFOLIO_DIAGRAMS
    ):
        path = ROOT / path_text
        if not path.is_file():
            errors.append(f"Missing Milestone 14 portfolio file: {path_text}")
        elif developer_path in path.read_text(encoding="utf-8", errors="ignore"):
            errors.append(f"Milestone 14 file contains local absolute path: {path_text}")

    audit = ROOT / "reports/portfolio/milestone_audit.json"
    integrity = ROOT / "reports/portfolio/evidence_integrity.json"
    inventory = ROOT / "reports/portfolio/initial_commit_inventory.json"
    readiness = ROOT / "reports/portfolio/portfolio_readiness.json"
    remote_ci = ROOT / "reports/assurance/remote_ci_validation.json"
    registry = ROOT / "models/registry.json"
    retraining = ROOT / "reports/retraining/retraining_recommendation.json"

    if audit.is_file():
        payload = _load_json(audit)
        if payload.get("result") != "passed":
            errors.append("Milestone audit must pass.")
        statuses = {
            item.get("number"): item.get("status") for item in payload.get("milestones", [])
        }
        if statuses.get(4) != "complete_with_external_blocker":
            errors.append("Milestone 4 must remain externally blocked.")
        if statuses.get(8) != "complete_with_external_blocker":
            errors.append("Milestone 8 must remain externally blocked.")
        if statuses.get(14) != "complete":
            errors.append("Milestone 14 must be complete.")
    if integrity.is_file() and _load_json(integrity).get("result") != "passed":
        errors.append("Evidence integrity audit must pass.")
    if inventory.is_file():
        payload = _load_json(inventory)
        if payload.get("commit_eligible") is not True:
            errors.append("Initial commit inventory must be eligible.")
        if payload.get("large_files") or payload.get("binary_files"):
            errors.append("Initial commit inventory must not include large or binary files.")
    if readiness.is_file():
        payload = _load_json(readiness)
        if payload.get("local_review_ready") is not True:
            errors.append("Portfolio readiness must report local review ready.")
        if payload.get("operational_release_ready") is not False:
            errors.append("Portfolio readiness must keep operational release blocked.")
        if payload.get("model_approval_status") != "pending":
            errors.append("Portfolio readiness must keep approval pending.")
        if payload.get("model_activation_status") != "inactive":
            errors.append("Portfolio readiness must keep activation inactive.")
    if remote_ci.is_file():
        payload = _load_json(remote_ci)
        if payload.get("remote_ci_executed") is True:
            for workflow in payload.get("workflows", []):
                if not workflow.get("run_id") or not str(workflow.get("run_url", "")).startswith(
                    "https://github.com/"
                ):
                    errors.append(
                        "Executed remote CI evidence must include genuine run IDs and URLs."
                    )
        elif payload.get("workflows"):
            errors.append("Pre-push remote CI evidence must not fabricate workflow runs.")
    if registry.is_file():
        payload = _load_json(registry)
        version = payload.get("models", [{}])[0].get("versions", [{}])[0]
        if version.get("registry_version") != 1:
            errors.append("Registry version 1 must be preserved.")
        if version.get("approval_decision") is not None:
            errors.append("Model approval must remain pending.")
        if version.get("activation_event") is not None:
            errors.append("Model activation must remain inactive.")
    if retraining.is_file():
        payload = _load_json(retraining)
        if payload.get("recommendation") != "retain_champion":
            errors.append("Retraining recommendation must remain retain_champion.")
        if payload.get("automatic_action") != "none":
            errors.append("Retraining automatic action must remain none.")
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for phrase in [
        "executive summary",
        "operational release readiness: blocked",
        "model approval granted: no",
        "model activation performed: no",
    ]:
        if phrase not in readme:
            errors.append(f"README missing final portfolio phrase: {phrase}")
    return errors


def _load_json(path: Path) -> dict[str, Any]:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain a JSON object.")
    return payload


def run(selected: set[str]) -> int:
    checkout_safe = {
        "structure",
        "docs",
        "config",
        "boundaries",
        "release_workflows",
        "release_shell",
        "release_containers",
    }
    checks = {
        "structure": validate_structure,
        "docs": validate_docs,
        "config": validate_config,
        "boundaries": validate_boundaries,
        "synthetic": validate_synthetic_data_foundation,
        "database": validate_database_foundation,
        "features": validate_feature_foundation,
        "models": validate_model_foundation,
        "registry": validate_registry_foundation,
        "rshiny": validate_rshiny_foundation,
        "monitoring": validate_monitoring_foundation,
        "retraining": validate_retraining_foundation,
        "release": validate_release_foundation,
        "release_workflows": validate_release_workflows,
        "release_shell": validate_release_shell,
        "release_containers": validate_release_containers,
        "portfolio": validate_portfolio_foundation,
    }
    active = checkout_safe if "checkout_safe" in selected else selected or set(checks)
    errors: list[str] = []
    for name, check in checks.items():
        if name in active:
            check_errors = check()
            if check_errors:
                errors.extend(f"[{name}] {error}" for error in check_errors)
            else:
                print(f"[{name}] ok")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--structure", action="store_true", help="Validate required files/directories."
    )
    parser.add_argument("--docs", action="store_true", help="Validate documentation presence.")
    parser.add_argument("--config", action="store_true", help="Validate YAML configuration.")
    parser.add_argument(
        "--boundaries", action="store_true", help="Validate Milestone 1 boundaries."
    )
    parser.add_argument("--synthetic", action="store_true", help="Validate Milestone 2 assets.")
    parser.add_argument("--database", action="store_true", help="Validate Milestone 3 assets.")
    parser.add_argument("--features", action="store_true", help="Validate Milestone 5 assets.")
    parser.add_argument("--models", action="store_true", help="Validate Milestone 6 assets.")
    parser.add_argument("--registry", action="store_true", help="Validate Milestone 7 assets.")
    parser.add_argument("--rshiny", action="store_true", help="Validate Milestone 9 assets.")
    parser.add_argument(
        "--monitoring", action="store_true", help="Validate Milestone 11 monitoring assets."
    )
    parser.add_argument(
        "--retraining", action="store_true", help="Validate Milestone 12 retraining assets."
    )
    parser.add_argument("--release", action="store_true", help="Validate Milestone 13 assets.")
    parser.add_argument(
        "--release-workflows",
        dest="release_workflows",
        action="store_true",
        help="Validate Milestone 13 workflow files.",
    )
    parser.add_argument(
        "--release-shell",
        dest="release_shell",
        action="store_true",
        help="Validate Milestone 13 shell scripts.",
    )
    parser.add_argument(
        "--release-containers",
        dest="release_containers",
        action="store_true",
        help="Validate Milestone 13 Docker and Compose files.",
    )
    parser.add_argument("--portfolio", action="store_true", help="Validate Milestone 14 assets.")
    parser.add_argument(
        "--checkout-safe",
        dest="checkout_safe",
        action="store_true",
        help="Validate only checks that are safe before ignored generated artefacts exist.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected = {
        name
        for name in (
            "structure",
            "docs",
            "config",
            "boundaries",
            "synthetic",
            "database",
            "features",
            "models",
            "registry",
            "rshiny",
            "monitoring",
            "retraining",
            "release",
            "release_workflows",
            "release_shell",
            "release_containers",
            "portfolio",
            "checkout_safe",
        )
        if getattr(args, name)
    }
    return run(selected)


if __name__ == "__main__":
    raise SystemExit(main())
