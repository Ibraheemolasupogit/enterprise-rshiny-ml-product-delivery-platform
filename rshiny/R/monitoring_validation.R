validate_monitoring_evidence <- function(evidence) {
  required <- c(
    "baseline", "run", "schema", "data_quality", "numeric", "categorical",
    "missingness", "prediction", "performance", "calibration", "operational",
    "alerts", "review", "summary"
  )
  missing <- setdiff(required, names(evidence))
  if (length(missing) > 0) {
    stop("Monitoring evidence is incomplete.", call. = FALSE)
  }
  if (!identical(evidence$run$candidate_identifier, evidence$baseline$candidate_identifier)) {
    stop("Monitoring candidate identifier mismatch.", call. = FALSE)
  }
  if (!identical(evidence$review$registry_mutation_status, "none")) {
    stop("Monitoring evidence must not mutate registry state.", call. = FALSE)
  }
  actions <- unlist(evidence$alerts$automatic_action_values %||% list("none"))
  if (any(!actions %in% c("none", "human_review_required"))) {
    stop("Monitoring evidence contains prohibited automatic action.", call. = FALSE)
  }
  invisible(TRUE)
}
