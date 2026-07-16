load_app_config <- function(path = file.path("config", "rshiny.yaml")) {
  if (!requireNamespace("yaml", quietly = TRUE)) {
    stop("yaml package is required", call. = FALSE)
  }
  path <- resolve_config_path(path)
  payload <- yaml::read_yaml(path)
  validate_app_config(payload)
  payload
}

resolve_config_path <- function(path) {
  if (file.exists(path)) {
    return(path)
  }
  candidates <- file.path(c("..", "../..", "../../.."), path)
  for (candidate in candidates) {
    if (file.exists(candidate)) {
      return(candidate)
    }
  }
  path
}

validate_app_config <- function(config) {
  required_top <- c("version", "description", "implementation_status", "enabled",
                    "application", "api", "features", "cohort_scoring",
                    "performance", "governance", "review_mode", "feedback")
  reject_unknown_names(config, required_top, "rshiny config")
  stopifnot_identical(config$implementation_status, "implemented", "implementation_status")
  stopifnot_identical(config$enabled, TRUE, "enabled")
  stopifnot_identical(config$application$environment, "local", "application.environment")
  stopifnot_identical(config$review_mode$allow_ui_toggle, FALSE, "review_mode.allow_ui_toggle")
  expected_features <- c(
    "overview", "single_prediction", "cohort_scoring", "performance_dashboard",
    "model_governance", "feedback", "monitoring", "drift_detection", "retraining",
    "governance_admin", "deployment_controls"
  )
  reject_unknown_names(config$features, expected_features, "feature flag")
  enabled <- c("overview", "single_prediction", "cohort_scoring", "performance_dashboard",
               "model_governance", "monitoring", "feedback")
  for (feature in enabled) {
    stopifnot_identical(config$features[[feature]], TRUE, paste0("features.", feature))
  }
  disabled <- c("drift_detection", "retraining", "governance_admin", "deployment_controls")
  for (feature in disabled) {
    stopifnot_identical(config$features[[feature]], FALSE, paste0("features.", feature))
  }
  validate_cohort_config(config$cohort_scoring)
  stopifnot_identical(config$performance$source, "committed_model_evidence", "performance.source")
  stopifnot_identical(config$performance$allow_live_metric_recalculation, FALSE,
                      "performance.allow_live_metric_recalculation")
  stopifnot_identical(config$governance$source, "registry_and_governance_evidence",
                      "governance.source")
  stopifnot_identical(config$governance$allow_state_changes, FALSE,
                      "governance.allow_state_changes")
  validate_relative_output_path(config$feedback$output_path)
  invisible(TRUE)
}

validate_cohort_config <- function(config) {
  reject_unknown_names(
    config,
    c("maximum_rows", "accepted_formats", "maximum_file_size_mb", "export_enabled",
      "retain_uploads"),
    "cohort scoring config"
  )
  if (!is.numeric(config$maximum_rows) || config$maximum_rows < 1 || config$maximum_rows > 100) {
    stop("cohort_scoring.maximum_rows must be between 1 and 100", call. = FALSE)
  }
  formats <- unlist(config$accepted_formats)
  if (!identical(formats, "csv")) {
    stop("cohort_scoring.accepted_formats must only allow csv", call. = FALSE)
  }
  if (!is.numeric(config$maximum_file_size_mb) || config$maximum_file_size_mb > 2) {
    stop("cohort_scoring.maximum_file_size_mb must be 2 or less", call. = FALSE)
  }
  stopifnot_identical(config$export_enabled, TRUE, "cohort_scoring.export_enabled")
  stopifnot_identical(config$retain_uploads, FALSE, "cohort_scoring.retain_uploads")
  invisible(TRUE)
}

reject_unknown_names <- function(value, expected, label) {
  unknown <- setdiff(names(value), expected)
  if (length(unknown) > 0) {
    stop(sprintf("Unknown %s field(s): %s", label, paste(unknown, collapse = ", ")),
         call. = FALSE)
  }
}

stopifnot_identical <- function(value, expected, label) {
  if (!identical(value, expected)) {
    stop(sprintf("%s must be %s", label, as.character(expected)), call. = FALSE)
  }
}

validate_relative_output_path <- function(path) {
  if (!is.character(path) || length(path) != 1 || path == "") {
    stop("feedback.output_path must be a non-empty string", call. = FALSE)
  }
  if (grepl("^/", path) || grepl("(^|/)\\.\\.(/|$)", path)) {
    stop("feedback.output_path must stay inside the repository", call. = FALSE)
  }
  if (!startsWith(path, "data/monitoring/")) {
    stop("feedback.output_path must use data/monitoring", call. = FALSE)
  }
  invisible(TRUE)
}

api_client_from_env <- function(config = load_app_config()) {
  base_url <- Sys.getenv(config$api$base_url_environment_variable, "http://127.0.0.1:8000")
  api_key <- Sys.getenv(config$api$api_key_environment_variable, "")
  timeout <- as.numeric(Sys.getenv("SHINY_REQUEST_TIMEOUT_SECONDS",
                                   as.character(config$api$timeout_seconds)))
  validate_api_base_url(base_url)
  list(base_url = sub("/+$", "", base_url), api_key = api_key, timeout = timeout)
}
