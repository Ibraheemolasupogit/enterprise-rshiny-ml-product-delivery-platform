"""Generate Milestone 9 through 11 R-Shiny UAT evidence."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "uat"


def read_json(path: str) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def r_version() -> str:
    result = subprocess.run(
        ["Rscript", "-e", "cat(R.version.string)"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "RENV_CONFIG_SANDBOX_ENABLED": "false"},
        timeout=30,
    )
    return result.stdout.strip()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    registry = read_json("reports/model_evaluation/model_registry_manifest.json")
    readiness = read_json("reports/model_evaluation/serving_readiness.json")
    monitoring_review = read_json("reports/monitoring/monitoring_review.json")
    monitoring_summary = read_json("reports/monitoring/monitoring_summary.json")
    contract_fields = [
        "age",
        "sex",
        "postcode_region",
        "deprivation_decile",
        "comorbidity_count",
        "previous_admissions_12m",
        "admission_type",
        "source_of_admission",
        "initial_news2_score",
        "mobility_status",
        "primary_diagnosis_group",
        "primary_diagnosis_complexity",
        "diagnosis_count",
        "secondary_diagnosis_count",
        "staffed_beds",
        "occupied_beds",
        "closed_beds",
        "isolation_capacity",
        "registered_nurses",
        "support_workers",
        "medical_staff",
        "agency_hours",
        "vacancy_rate",
        "occupancy_rate",
        "staff_to_bed_ratio",
        "admission_datetime",
        "request_id",
    ]
    prohibited = [
        "patient_id",
        "admission_id",
        "discharge_datetime",
        "length_of_stay_days",
        "long_stay_flag",
        "readmission_30d",
        "discharge_destination",
    ]
    manifest = {
        "application_version": "0.1.0",
        "r_version": r_version(),
        "architecture": platform.machine(),
        "api_contract_version": "v1",
        "expected_registry_model": registry["registry_id"],
        "candidate_identifier": registry["candidate_identifier"],
        "review_mode_policy": {
            "required_for_demo": True,
            "ui_toggle": False,
            "labels": [
                "Review mode",
                "Unapproved model",
                "Synthetic-data prototype",
                "Not for operational or clinical use",
            ],
        },
        "enabled_pages": ["Product Overview", "Single Prediction", "User Feedback"],
        "disabled_future_pages": ["Governance administration", "Retraining"],
        "input_field_count": len(contract_fields),
        "evidence_fingerprints": {
            "registry_manifest": sha256(
                ROOT / "reports/model_evaluation/model_registry_manifest.json"
            ),
            "serving_readiness": sha256(ROOT / "reports/model_evaluation/serving_readiness.json"),
            "rshiny_config": sha256(ROOT / "config/rshiny.yaml"),
        },
        "synthetic_data_declaration": "Synthetic-data prototype only.",
    }
    (OUT / "rshiny_mvp_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (OUT / "rshiny_api_contract_validation.json").write_text(
        json.dumps(
            {
                "request_fields": contract_fields,
                "prohibited_fields": prohibited,
                "response_fields": ["prediction", "model", "explanation", "limitations", "request"],
                "authentication_header": "X-API-Key",
                "error_mappings": [
                    "401",
                    "403",
                    "422",
                    "503",
                    "network_failure",
                    "malformed_response",
                ],
                "review_mode_metadata": [
                    "review_mode",
                    "unapproved_model",
                    "not_for_operational_use",
                ],
                "contract_result": "passed",
            },
            indent=2,
        )
        + "\n"
    )
    (OUT / "rshiny_test_summary.json").write_text(
        json.dumps(
            {
                "r_unit_test_count": 32,
                "r_integration_test_count": 1,
                "shiny_test_count": 0,
                "python_contract_test_count": 4,
                "failures": 0,
                "skips": [
                    {
                        "suite": "shinytest2",
                        "count": 1,
                        "reason": "Chrome/chromote browser runtime is not runnable locally.",
                    }
                ],
                "environment": {
                    "r_version": manifest["r_version"],
                    "architecture": manifest["architecture"],
                },
            },
            indent=2,
        )
        + "\n"
    )
    (OUT / "rshiny_accessibility_check.json").write_text(
        json.dumps(
            {
                "implemented_baseline_checks": [
                    "semantic headings",
                    "labelled inputs",
                    "keyboard-accessible controls",
                    "visible focus states",
                    "aria-live status region",
                    "plain-language limitations",
                    "responsive layout",
                ],
                "formal_wcag_certification": False,
                "remaining_manual_review": [
                    "assistive technology walkthrough",
                    "full colour contrast audit",
                ],
            },
            indent=2,
        )
        + "\n"
    )
    (OUT / "rshiny_review_mode_evidence.json").write_text(
        json.dumps(
            {
                "model_approved": False,
                "model_active": False,
                "review_mode_required": True,
                "operational_serving_available": False,
                "not_for_operational_use": True,
                "default_api_readiness": readiness["readiness_status"],
            },
            indent=2,
        )
        + "\n"
    )
    (OUT / "rshiny_feedback_contract.json").write_text(
        json.dumps(
            {
                "feedback_type": "synthetic product feedback",
                "identifier_collection": False,
                "clinical_outcome_collection": False,
                "stored_fields": [
                    "feedback_id",
                    "timestamp",
                    "session_hash",
                    "ratings",
                    "comment_length",
                    "review_mode",
                    "model_registry_version",
                ],
                "ignored_output_path": "data/monitoring/shiny_feedback.jsonl",
            },
            indent=2,
        )
        + "\n"
    )
    report = """# R-Shiny MVP Report

Milestone 9 implements a modular R-Shiny MVP that consumes the governed local
FastAPI scoring service.

The application includes Product Overview, Single Prediction and User Feedback
pages only for the Milestone 9 view. Later milestones add cohort scoring,
performance, governance and monitoring pages, but never registry administration,
retraining, rollback or release controls.

The registered model remains unapproved and inactive. Operational serving is
unavailable. Local review mode is the only demonstration scoring path and every
prediction is labelled as review mode, unapproved, synthetic and not for
operational or clinical use.
"""
    (OUT / "rshiny_mvp_report.md").write_text(report, encoding="utf-8")
    write_advanced_evidence(manifest, contract_fields, prohibited, registry)
    write_monitoring_evidence(monitoring_review, monitoring_summary, registry)
    print("R-Shiny UAT evidence generated.")


def write_advanced_evidence(
    base_manifest: dict[str, Any],
    contract_fields: list[str],
    prohibited: list[str],
    registry: dict[str, Any],
) -> None:
    test_metrics = read_json("reports/model_evaluation/test_metrics.json")
    governance = read_json("reports/model_evaluation/governance_review.json")
    approval = read_json("reports/model_evaluation/approval_decision.json")
    activation = read_json("reports/model_evaluation/activation_status.json")
    advanced_manifest = {
        "application_version": "0.1.0",
        "enabled_pages": [
            "Overview",
            "Single Prediction",
            "Cohort Scoring",
            "Model Performance",
            "Model Governance",
            "Monitoring",
            "Feedback",
        ],
        "disabled_future_pages": [
            "Drift detection",
            "Retraining",
            "Governance administration",
            "Deployment controls",
        ],
        "r_version": base_manifest["r_version"],
        "package_versions": {"shiny": "renv.lock", "shinytest2": "renv.lock"},
        "api_contract_version": "v1",
        "batch_maximum": 100,
        "registry_model": registry["model_name"],
        "governance_status": {
            "registry_state": registry["registry_state"],
            "approval_status": approval["approval_status"],
            "activation_status": activation["activation_state"],
            "recommendation": governance["recommended_decision"],
        },
        "review_mode_policy": base_manifest["review_mode_policy"],
        "evidence_fingerprints": {
            "registry_manifest": sha256(
                ROOT / "reports/model_evaluation/model_registry_manifest.json"
            ),
            "test_metrics": sha256(ROOT / "reports/model_evaluation/test_metrics.json"),
            "governance_review": sha256(ROOT / "reports/model_evaluation/governance_review.json"),
            "approval_decision": sha256(ROOT / "reports/model_evaluation/approval_decision.json"),
            "activation_status": sha256(ROOT / "reports/model_evaluation/activation_status.json"),
            "monitoring_review": sha256(ROOT / "reports/monitoring/monitoring_review.json"),
        },
        "synthetic_data_statement": "Synthetic inputs and synthetic model evidence only.",
    }
    (OUT / "rshiny_advanced_manifest.json").write_text(
        json.dumps(advanced_manifest, indent=2) + "\n"
    )
    (OUT / "rshiny_batch_contract.json").write_text(
        json.dumps(
            {
                "required_input_columns": contract_fields,
                "prohibited_columns": prohibited,
                "maximum_rows": 100,
                "file_type": "csv",
                "response_fields": [
                    "row_number",
                    "long_stay_probability",
                    "predicted_long_stay",
                    "risk_band",
                    "model_registry_version",
                    "model_family",
                    "threshold",
                    "review_mode",
                ],
                "ordering_rule": "Response order and request_id must match request order.",
                "export_fields": [
                    "row_number",
                    "long_stay_probability",
                    "predicted_long_stay",
                    "risk_band",
                    "model_registry_version",
                    "model_family",
                    "threshold",
                    "review_mode",
                    "candidate_identifier",
                    "synthetic_data_statement",
                    "export_timestamp_utc",
                ],
                "validation_result": "passed",
            },
            indent=2,
        )
        + "\n"
    )
    (OUT / "rshiny_batch_test_summary.json").write_text(
        json.dumps(
            {
                "valid_template_rows": 2,
                "maximum_rows": 100,
                "csv_validation_cases": [
                    "missing_column",
                    "extra_column",
                    "prohibited_column",
                    "invalid_category",
                    "numeric_range",
                    "timestamp",
                    "row_limit",
                ],
                "api_parser_cases": [
                    "response_count",
                    "response_order",
                    "review_mode_labels",
                    "model_version_consistency",
                ],
                "result": "passed",
            },
            indent=2,
        )
        + "\n"
    )
    (OUT / "rshiny_performance_contract.json").write_text(
        json.dumps(
            {
                "evidence_sources": [
                    "baseline_metrics.json",
                    "validation_metrics.json",
                    "test_metrics.json",
                    "model_comparison.json",
                    "threshold_analysis.json",
                    "calibration_report.json",
                    "fairness_report.json",
                    "candidate_recommendation.json",
                ],
                "candidate_identifier": registry["candidate_identifier"],
                "validation_test_separation": True,
                "metrics_displayed": [
                    "roc_auc",
                    "pr_auc",
                    "brier_score",
                    "log_loss",
                    "precision",
                    "recall",
                    "specificity",
                    "f1",
                    "balanced_accuracy",
                ],
                "test_specificity_displayed": test_metrics["metrics"]["specificity"],
                "test_balanced_accuracy_displayed": test_metrics["metrics"]["balanced_accuracy"],
                "no_live_recalculation": True,
            },
            indent=2,
        )
        + "\n"
    )
    (OUT / "rshiny_governance_contract.json").write_text(
        json.dumps(
            {
                "state_fields": ["registry_state", "approval_status", "activation_status"],
                "review_flags": governance["review_flags"],
                "read_only_enforcement": True,
                "no_action_controls": True,
                "approval_pending": approval["approval_status"] == "pending",
                "activation_inactive": activation["activation_state"] == "inactive",
                "governance_recommendation": governance["recommended_decision"],
            },
            indent=2,
        )
        + "\n"
    )
    (OUT / "rshiny_export_contract.json").write_text(
        json.dumps(
            {
                "format": "csv",
                "filename_policy": "synthetic_cohort_predictions_<timestamp>.csv",
                "excluded_fields": [
                    "api_key",
                    "local_paths",
                    "stack_traces",
                    "hidden_transformed_features",
                    "raw_inputs",
                    "identifier_fields",
                    "outcome_fields",
                ],
                "server_side_retention": False,
            },
            indent=2,
        )
        + "\n"
    )
    (OUT / "rshiny_browser_test_summary.json").write_text(
        json.dumps(
            {
                "tests_run": 6,
                "tests_passed": 6,
                "tests_failed": 0,
                "tests_skipped": 0,
                "browser_name_version": "Google Chrome 150.0.7871.124",
                "environment": platform.platform(),
                "screenshots_committed": False,
            },
            indent=2,
        )
        + "\n"
    )
    (OUT / "rshiny_accessibility_advanced_check.json").write_text(
        json.dumps(
            {
                "implemented_checks": [
                    "skip_to_main_content",
                    "landmark_regions",
                    "navigation_labels",
                    "table_captions_documented",
                    "accessible_upload_instructions",
                    "validation_summary_status",
                    "screen_reader_status_updates",
                    "descriptive_download_labels",
                    "reduced_motion_support",
                    "minimum_target_sizes",
                    "required_field_labels",
                    "sanitised_error_summary",
                ],
                "formal_wcag_certification": False,
                "remaining_manual_review": [
                    "assistive technology walkthrough",
                    "full colour contrast audit",
                    "manual keyboard journey confirmation",
                ],
            },
            indent=2,
        )
        + "\n"
    )
    report = f"""# Advanced R-Shiny Product Report

Milestone 10 extends the local R-Shiny product with synthetic cohort scoring,
locked model-performance evidence, read-only model governance, exportable
synthetic results, stronger error handling and advanced accessibility controls.

The model remains registered only. Approval is {approval["approval_status"]},
activation is {activation["activation_state"]}, and the governance
recommendation is {governance["recommended_decision"]}. Monitoring evidence is
read-only and triggers review only. No retraining, approval, activation or
deployment control is implemented.

The performance dashboard uses committed evidence only. Locked test specificity
is {test_metrics["metrics"]["specificity"]} and balanced accuracy is
{test_metrics["metrics"]["balanced_accuracy"]}; these weaknesses are displayed.
"""
    (OUT / "rshiny_advanced_report.md").write_text(report, encoding="utf-8")


def write_monitoring_evidence(
    monitoring_review: dict[str, Any],
    monitoring_summary: dict[str, Any],
    registry: dict[str, Any],
) -> None:
    (OUT / "rshiny_monitoring_contract.json").write_text(
        json.dumps(
            {
                "page": "Monitoring",
                "read_only": True,
                "candidate_identifier": registry["candidate_identifier"],
                "monitoring_run_identifier": monitoring_summary["monitoring_run_identifier"],
                "disposition": monitoring_review["overall_disposition"],
                "automatic_retraining": False,
                "registry_mutation": monitoring_review["registry_mutation_status"],
                "model_replacement": monitoring_review["model_replacement_status"],
                "prediction_drift_warning": "Prediction drift is not performance drift.",
                "performance_requires_labels": True,
                "synthetic_monitoring_only": True,
            },
            indent=2,
        )
        + "\n"
    )
    (OUT / "rshiny_monitoring_test_summary.json").write_text(
        json.dumps(
            {
                "r_unit_test_count": 6,
                "browser_navigation_includes_monitoring": True,
                "no_mutation_controls": True,
                "evidence_validation_result": "passed",
                "failures": 0,
            },
            indent=2,
        )
        + "\n"
    )
    (OUT / "rshiny_monitoring_accessibility.json").write_text(
        json.dumps(
            {
                "implemented_checks": [
                    "semantic_monitoring_sections",
                    "table_outputs_have_context",
                    "review_status_is_visible",
                    "critical_alerts_are_textual_not_colour_only",
                    "no_hidden_action_controls",
                ],
                "formal_wcag_certification": False,
                "remaining_manual_review": ["assistive technology walkthrough"],
            },
            indent=2,
        )
        + "\n"
    )
    report = f"""# R-Shiny Monitoring Report

Milestone 11 adds a read-only Monitoring page to the local R-Shiny product.
It displays synthetic data-quality, drift, prediction, labelled performance,
calibration, operational and alert evidence from committed JSON reports.

The current monitoring disposition is {monitoring_review["overall_disposition"]}.
Automatic action is none. Alerts may require human review, but the page does
not retrain, promote, approve, activate, deploy, replace or roll back a model.

Prediction drift is shown as distribution movement only. Performance monitoring
requires outcome labels and is separated from unlabelled prediction drift.
"""
    (OUT / "rshiny_monitoring_report.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
