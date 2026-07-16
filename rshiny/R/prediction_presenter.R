present_prediction <- function(response) {
  if (!isTRUE(response$ok)) {
    return(list(ok = FALSE, message = response$message, code = response$code))
  }
  data <- response$data
  validate_prediction_response(data)
  probability <- data$prediction$long_stay_probability
  list(
    ok = TRUE,
    probability_label = sprintf("The model estimated a synthetic long-stay probability of %.2f.", probability),
    class_label = if (isTRUE(data$prediction$predicted_long_stay)) "Above selected threshold" else "Below selected threshold",
    risk_band = data$prediction$risk_band,
    threshold = data$model$threshold,
    model_family = data$model$model_family,
    registry_version = data$model$registry_version,
    candidate_identifier = data$model$candidate_identifier,
    calibration = data$model$calibration,
    approval_status = data$model$approval_status,
    activation_status = data$model$activation_status,
    review_mode = isTRUE(data$request$review_mode),
    request_id = data$request$request_id,
    status = paste(data$request$status, collapse = ", "),
    factors = data$explanation$important_factors,
    explanation_method = data$explanation$method,
    explanation_warning = data$explanation$warning,
    limitations = data$limitations
  )
}

validate_prediction_response <- function(data) {
  required <- c("prediction", "model", "explanation", "limitations", "request")
  missing <- setdiff(required, names(data))
  if (length(missing) > 0) {
    stop(sprintf("Prediction response missing: %s", paste(missing, collapse = ", ")),
         call. = FALSE)
  }
  probability <- data$prediction$long_stay_probability
  if (!is.numeric(probability) || probability < 0 || probability > 1) {
    stop("Prediction probability must be between 0 and 1", call. = FALSE)
  }
  required_status <- c("review_mode", "unapproved_model", "not_for_operational_use")
  if (isTRUE(data$request$review_mode) &&
        !all(required_status %in% data$request$status)) {
    stop("Review-mode response is missing required labels", call. = FALSE)
  }
  invisible(TRUE)
}

status_text <- function(status) {
  ready <- status$ready
  model <- status$model
  if (isTRUE(ready$ok) && isTRUE(ready$data$review_mode)) {
    return("LOCAL REVIEW MODE - This application is using a registered but unapproved synthetic model. It is not approved for operational or clinical use.")
  }
  if (isTRUE(model$ok) && isTRUE(model$data$available)) {
    return("MODEL AVAILABLE - Check governance status before use.")
  }
  "SCORING UNAVAILABLE - No approved active model is available. The application can display product information but cannot generate predictions."
}
