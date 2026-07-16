api_request <- function(client, method, path, body = NULL) {
  if (identical(client$api_key, "")) {
    return(api_error("authentication_error", 401,
                     "The application could not authenticate with the scoring service."))
  }
  req <- httr2::request(paste0(client$base_url, path)) |>
    httr2::req_method(method) |>
    httr2::req_headers("X-API-Key" = client$api_key, "Accept" = "application/json") |>
    httr2::req_timeout(client$timeout)
  if (!is.null(body)) {
    req <- httr2::req_body_json(req, body, auto_unbox = TRUE)
  }
  tryCatch({
    resp <- httr2::req_perform(req, path = NULL)
    parse_api_response(resp)
  }, error = function(err) {
    api_error(
      "api_unavailable",
      NA_integer_,
      "The scoring service is currently unavailable. No prediction was generated."
    )
  })
}

parse_api_response <- function(resp) {
  status <- httr2::resp_status(resp)
  if (status >= 200 && status < 300) {
    data <- tryCatch(httr2::resp_body_json(resp, simplifyVector = FALSE),
                     error = function(err) NULL)
    if (is.null(data)) {
      return(api_error("malformed_response", status,
                       "The scoring service returned an unreadable response."))
    }
    return(list(ok = TRUE, status = status, data = data))
  }
  api_error(map_http_status(status), status, map_api_message(status),
            httr2::resp_header(resp, "x-request-id"))
}

api_error <- function(code, status, message, request_id = NULL) {
  list(ok = FALSE, code = code, status = status, message = message, request_id = request_id)
}

map_http_status <- function(status) {
  switch(as.character(status),
         "401" = "authentication_error",
         "403" = "authorisation_error",
         "422" = "validation_error",
         "413" = "batch_limit_error",
         "503" = "api_not_ready",
         "unexpected_error")
}

map_api_message <- function(status) {
  switch(as.character(status),
         "401" = "The application could not authenticate with the scoring service.",
         "403" = "The application could not authenticate with the scoring service.",
         "422" = "The request did not match the scoring service validation contract.",
         "503" = "The service is running, but no permitted model is ready for scoring.",
         "The scoring service returned an error. No prediction was generated.")
}

api_live <- function(client) {
  api_request(client, "GET", "/health/live")
}

api_ready <- function(client) {
  req <- httr2::request(paste0(client$base_url, "/health/ready")) |>
    httr2::req_timeout(client$timeout)
  tryCatch(
    parse_api_response(httr2::req_perform(req, path = NULL)),
    error = function(err) {
      api_error(
        "api_unavailable",
        NA_integer_,
        "The scoring service is currently unavailable."
      )
    }
  )
}

api_model_metadata <- function(client) {
  api_request(client, "GET", "/v1/model")
}

api_registry_status <- function(client) {
  api_request(client, "GET", "/v1/registry/status")
}

api_predict <- function(client, record) {
  api_request(client, "POST", "/v1/predict", build_prediction_payload(record))
}

api_predict_batch <- function(client, records, config = load_app_config()) {
  if (length(records) > config$cohort_scoring$maximum_rows) {
    return(api_error(
      "batch_limit_error",
      413,
      "The synthetic cohort exceeds the configured batch limit."
    ))
  }
  payload <- list(records = lapply(records, build_prediction_payload))
  api_request(client, "POST", "/v1/predict/batch", payload)
}

api_submit_feedback <- function(feedback, config = load_app_config(), status = list()) {
  write_feedback_record(feedback, config, status)
}

fetch_service_status <- function(client) {
  ready <- api_ready(client)
  model <- api_model_metadata(client)
  registry <- api_registry_status(client)
  list(ready = ready, model = model, registry = registry)
}
