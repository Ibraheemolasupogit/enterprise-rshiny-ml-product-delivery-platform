validate_retraining_evidence <- function(evidence) {
  required <- c("eligibility", "dataset", "split", "training", "champion", "challengers",
                "comparison", "gates", "recommendation")
  missing <- setdiff(required, names(evidence))
  if (length(missing) > 0) {
    stop("Retraining evidence is incomplete.", call. = FALSE)
  }
  if (!identical(evidence$recommendation$approval_status, "not_granted")) {
    stop("Retraining evidence must not grant approval.", call. = FALSE)
  }
  if (!identical(evidence$recommendation$activation_status, "inactive")) {
    stop("Retraining evidence must not activate a model.", call. = FALSE)
  }
  if (!identical(evidence$recommendation$deployment_status, "not_performed")) {
    stop("Retraining evidence must not deploy a model.", call. = FALSE)
  }
  if (!identical(evidence$recommendation$automatic_action, "none")) {
    stop("Retraining evidence must not perform automatic action.", call. = FALSE)
  }
  if (!isTRUE(evidence$comparison$same_row_evaluation_confirmation)) {
    stop("Champion and challenger must be evaluated on the same rows.", call. = FALSE)
  }
  invisible(TRUE)
}
