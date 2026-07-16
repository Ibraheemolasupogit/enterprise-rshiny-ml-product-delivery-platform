"""Validate Milestone 12 advanced R-Shiny repository boundaries."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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
    "rshiny/modules/mod_governance.R",
    "rshiny/modules/mod_monitoring.R",
    "rshiny/modules/mod_retraining_review.R",
    "rshiny/modules/mod_feedback.R",
    "rshiny/modules/mod_status_banner.R",
    "rshiny/www/app.css",
    "rshiny/tests/testthat/test-contract.R",
    "rshiny/tests/testthat/test-api-client.R",
    "rshiny/tests/testthat/test-batch-contract.R",
    "rshiny/tests/testthat/test-evidence.R",
    "rshiny/tests/testthat/test-exports.R",
    "rshiny/tests/testthat/test-feedback.R",
    "rshiny/tests/testthat/test-monitoring.R",
    "rshiny/tests/testthat/test-retraining.R",
    "rshiny/www/sample_cohort_template.csv",
]

PROHIBITED_R_PATTERNS = [
    "reticulate::",
    "library(reticulate)",
    "xgboost",
    "randomForest",
    "DBI::",
    "duckdb::",
    "models/candidate",
    "models/registered",
    "long_stay_flag",
    "patient_id",
    "admission_id",
    "NHS",
]

REQUIRED_UAT_FILES = [
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


def main() -> None:
    missing = [path for path in REQUIRED_RSHINY_FILES if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"Missing R-Shiny files: {missing}")
    numbered_coverage = sorted(ROOT.glob(".coverage *"))
    if numbered_coverage:
        raise SystemExit(f"Disposable numbered coverage files must be removed: {numbered_coverage}")
    executable = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "rshiny/modules/mod_prediction.R",
            ROOT / "rshiny/modules/mod_batch_scoring.R",
            ROOT / "rshiny/modules/mod_performance.R",
            ROOT / "rshiny/modules/mod_governance.R",
            ROOT / "rshiny/R/api_client.R",
        ]
    )
    for pattern in PROHIBITED_R_PATTERNS:
        if pattern in executable:
            raise SystemExit(f"Prohibited R-Shiny implementation pattern found: {pattern}")
    if "allow_ui_toggle: false" not in (ROOT / "config/rshiny.yaml").read_text():
        raise SystemExit("Review mode UI toggle must remain disabled.")
    config = (ROOT / "config/rshiny.yaml").read_text()
    required_config = [
        "cohort_scoring: true",
        "performance_dashboard: true",
        "model_governance: true",
        "monitoring: true",
        "drift_detection: false",
        "retraining: false",
        "governance_admin: false",
        "deployment_controls: false",
        "retain_uploads: false",
        "allow_state_changes: false",
    ]
    for snippet in required_config:
        if snippet not in config:
            raise SystemExit(f"Missing R-Shiny config boundary: {snippet}")
    app_text = (ROOT / "rshiny/app.R").read_text()
    if "Monitoring" not in app_text:
        raise SystemExit("Monitoring page must be exposed for Milestone 11.")
    if "Retraining Review" not in app_text:
        raise SystemExit("Retraining Review page must be exposed for Milestone 12.")
    for forbidden in ["Drift"]:
        if forbidden in app_text:
            raise SystemExit(f"Future page must not be exposed: {forbidden}")
    monitoring_text = (ROOT / "rshiny/modules/mod_monitoring.R").read_text()
    for control in ["Retrain", "Promote", "Activate", "Approve", "Deploy", "Rollback"]:
        if control in monitoring_text:
            raise SystemExit(f"Monitoring mutation control must be absent: {control}")
    for snippet in [
        "Prediction drift is not performance drift without outcome labels.",
        "Performance monitoring requires outcome labels.",
        "Automatic action is none",
    ]:
        if snippet not in monitoring_text:
            raise SystemExit(f"Monitoring page missing boundary text: {snippet}")
    retraining_text = (ROOT / "rshiny/modules/mod_retraining_review.R").read_text()
    for control in ["actionButton", "downloadButton", "Run retraining", "Register challenger"]:
        if control in retraining_text:
            raise SystemExit(f"Retraining mutation control must be absent: {control}")
    for snippet in [
        "This page displays retraining evidence only.",
        "It cannot retrain, register, approve, activate or deploy a model.",
        "Automatic action is none",
    ]:
        if snippet not in retraining_text:
            raise SystemExit(f"Retraining page missing boundary text: {snippet}")
    gov_text = (ROOT / "rshiny/modules/mod_governance.R").read_text()
    for control in ["Approve", "Reject", "Activate", "Retire", "Roll back", "Register", "Deploy"]:
        if control in gov_text:
            raise SystemExit(f"Governance mutation control must be absent: {control}")
    missing_uat = [path for path in REQUIRED_UAT_FILES if not (ROOT / path).exists()]
    if missing_uat:
        raise SystemExit(f"Missing advanced R-Shiny UAT evidence: {missing_uat}")
    print("Advanced R-Shiny boundary validation passed.")


if __name__ == "__main__":
    main()
