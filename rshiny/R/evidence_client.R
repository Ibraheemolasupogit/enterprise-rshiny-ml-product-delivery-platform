evidence_files <- list(
  baseline_metrics = "reports/model_evaluation/baseline_metrics.json",
  validation_metrics = "reports/model_evaluation/validation_metrics.json",
  test_metrics = "reports/model_evaluation/test_metrics.json",
  model_comparison = "reports/model_evaluation/model_comparison.json",
  threshold_analysis = "reports/model_evaluation/threshold_analysis.json",
  calibration_report = "reports/model_evaluation/calibration_report.json",
  fairness_report = "reports/model_evaluation/fairness_report.json",
  candidate_recommendation = "reports/model_evaluation/candidate_recommendation.json",
  registry_manifest = "reports/model_evaluation/model_registry_manifest.json",
  governance_review = "reports/model_evaluation/governance_review.json",
  approval_decision = "reports/model_evaluation/approval_decision.json",
  activation_status = "reports/model_evaluation/activation_status.json",
  registry_audit_summary = "reports/model_evaluation/registry_audit_summary.json",
  model_card = "reports/model_evaluation/model_card.md",
  registry = "models/registry.json"
)

read_evidence_json <- function(path) {
  resolved <- resolve_config_path(path)
  tryCatch(
    jsonlite::fromJSON(resolved, simplifyVector = FALSE),
    error = function(err) stop("Committed evidence could not be read.", call. = FALSE)
  )
}

load_model_evidence <- function() {
  evidence <- lapply(evidence_files[names(evidence_files) != "model_card"], read_evidence_json)
  evidence$model_card <- readLines(resolve_config_path(evidence_files$model_card), warn = FALSE)
  validate_model_evidence(evidence)
  evidence
}

validate_model_evidence <- function(evidence) {
  manifest <- evidence$registry_manifest
  recommendation <- evidence$candidate_recommendation
  test <- evidence$test_metrics
  approval <- evidence$approval_decision
  activation <- evidence$activation_status
  governance <- evidence$governance_review
  if (!identical(manifest$candidate_identifier, "CAND-85EA9202CAD6FE7F")) {
    stop("Evidence candidate identifier mismatch.", call. = FALSE)
  }
  if (!identical(as.integer(manifest$registry_version), 1L)) {
    stop("Evidence registry version mismatch.", call. = FALSE)
  }
  if (!identical(manifest$feature_build_identifier, "FBUILD-ADB1D374A8E41F8E")) {
    stop("Evidence feature build identifier mismatch.", call. = FALSE)
  }
  if (
    !identical(recommendation$test_set_used_for_selection, FALSE) ||
      !identical(test$test_set_used_for_selection, FALSE)
  ) {
    stop("Evidence must preserve locked test-set separation.", call. = FALSE)
  }
  if (
    !identical(approval$approval_status, "pending") ||
      !identical(activation$activation_state, "inactive") ||
      !identical(governance$recommended_decision, "defer")
  ) {
    stop("Evidence governance state is not pending/inactive/defer.", call. = FALSE)
  }
  metric_values <- unlist(test$metrics[setdiff(names(test$metrics), c(
    "confusion_matrix", "reliability_bins", "bootstrap_confidence_intervals",
    "calibration_intercept", "calibration_slope"
  ))])
  if (any(is.numeric(metric_values) & (metric_values < 0 | metric_values > 1), na.rm = TRUE)) {
    stop("Evidence contains metric values outside expected ranges.", call. = FALSE)
  }
  invisible(TRUE)
}

sanitize_path_text <- function(value) {
  gsub("([A-Za-z]:)?/?([^ ]*/)?(models|reports|data|Users)/[^, )]+", "[path redacted]", value)
}
