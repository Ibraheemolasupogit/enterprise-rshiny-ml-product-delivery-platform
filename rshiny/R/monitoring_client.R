monitoring_files <- list(
  baseline = "reports/monitoring/monitoring_baseline_manifest.json",
  run = "reports/monitoring/monitoring_run_manifest.json",
  schema = "reports/monitoring/schema_monitoring.json",
  data_quality = "reports/monitoring/data_quality_monitoring.json",
  numeric = "reports/monitoring/numeric_drift.json",
  categorical = "reports/monitoring/categorical_drift.json",
  missingness = "reports/monitoring/missingness_drift.json",
  prediction = "reports/monitoring/prediction_drift.json",
  performance = "reports/monitoring/performance_monitoring.json",
  calibration = "reports/monitoring/calibration_monitoring.json",
  operational = "reports/monitoring/operational_monitoring.json",
  alerts = "reports/monitoring/monitoring_alerts.json",
  review = "reports/monitoring/monitoring_review.json",
  summary = "reports/monitoring/monitoring_summary.json"
)

load_monitoring_evidence <- function() {
  evidence <- lapply(monitoring_files, read_evidence_json)
  validate_monitoring_evidence(evidence)
  evidence
}
