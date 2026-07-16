retraining_files <- list(
  eligibility = "reports/retraining/retraining_eligibility.json",
  dataset = "reports/retraining/retraining_dataset_manifest.json",
  split = "reports/retraining/retraining_split_summary.json",
  training = "reports/retraining/challenger_training_manifest.json",
  champion = "reports/retraining/champion_metrics.json",
  challengers = "reports/retraining/challenger_metrics.json",
  comparison = "reports/retraining/champion_challenger_comparison.json",
  calibration = "reports/retraining/challenger_calibration.json",
  thresholds = "reports/retraining/challenger_threshold_analysis.json",
  fairness = "reports/retraining/retraining_fairness_report.json",
  stability = "reports/retraining/retraining_stability_report.json",
  gates = "reports/retraining/promotion_gates.json",
  recommendation = "reports/retraining/retraining_recommendation.json",
  audit = "reports/retraining/retraining_audit_summary.json"
)

load_retraining_evidence <- function() {
  evidence <- lapply(retraining_files, read_evidence_json)
  validate_retraining_evidence(evidence)
  evidence
}
