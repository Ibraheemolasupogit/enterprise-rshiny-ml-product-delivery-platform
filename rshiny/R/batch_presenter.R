present_batch_predictions <- function(response, records) {
  if (!isTRUE(response$ok)) {
    return(list(ok = FALSE, message = response$message, code = response$code))
  }
  data <- response$data
  validate_batch_response(data, records)
  rows <- lapply(seq_along(data), function(i) {
    item <- data[[i]]
    data.frame(
      row_number = i,
      long_stay_probability = item$prediction$long_stay_probability,
      predicted_long_stay = isTRUE(item$prediction$predicted_long_stay),
      risk_band = item$prediction$risk_band,
      model_registry_version = item$model$registry_version,
      model_family = item$model$model_family,
      candidate_identifier = item$model$candidate_identifier,
      threshold = item$model$threshold,
      review_mode = isTRUE(item$request$review_mode),
      stringsAsFactors = FALSE
    )
  })
  results <- do.call(rbind, rows)
  list(ok = TRUE, results = results, summary = summarise_batch_results(results))
}

validate_batch_response <- function(data, records) {
  if (!is.list(data) || length(data) != length(records)) {
    stop("Batch response count did not match request count.", call. = FALSE)
  }
  versions <- character()
  for (i in seq_along(data)) {
    validate_prediction_response(data[[i]])
    if (!identical(data[[i]]$request$request_id, records[[i]]$request_id)) {
      stop("Batch response order did not match request order.", call. = FALSE)
    }
    versions <- c(versions, as.character(data[[i]]$model$registry_version))
  }
  if (length(unique(versions)) != 1) {
    stop("Batch response used inconsistent registry versions.", call. = FALSE)
  }
  invisible(TRUE)
}

summarise_batch_results <- function(results) {
  probabilities <- results$long_stay_probability
  list(
    records_scored = nrow(results),
    high_risk_count = sum(results$risk_band == "high"),
    predicted_positive_count = sum(results$predicted_long_stay),
    mean_probability = mean(probabilities),
    median_probability = stats::median(probabilities),
    min_probability = min(probabilities),
    max_probability = max(probabilities),
    risk_band_distribution = as.list(table(results$risk_band))
  )
}
