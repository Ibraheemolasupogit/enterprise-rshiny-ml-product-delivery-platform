test_that("HTTP status codes map to bounded user messages", {
  expect_equal(map_http_status(401), "authentication_error")
  expect_equal(map_http_status(403), "authorisation_error")
  expect_equal(map_http_status(422), "validation_error")
  expect_equal(map_http_status(413), "batch_limit_error")
  expect_equal(map_http_status(503), "api_not_ready")
  expect_false(grepl("MODEL_API_KEY", map_api_message(403)))
})

test_that("missing API key fails without exposing secrets", {
  client <- list(base_url = "http://127.0.0.1:9", api_key = "", timeout = 1)
  response <- api_request(client, "GET", "/v1/model")
  expect_false(response$ok)
  expect_equal(response$status, 401)
  expect_false(grepl("API_KEY", response$message))
})

test_that("prediction response parser requires review labels", {
  response <- list(
    ok = TRUE,
    data = list(
      prediction = list(long_stay_probability = 0.82, predicted_long_stay = TRUE, risk_band = "high"),
      model = list(model_family = "xgboost", registry_version = 1, candidate_identifier = "CAND-85EA9202CAD6FE7F",
                   calibration = "sigmoid", threshold = 0.75, approval_status = "pending",
                   activation_status = "registered"),
      explanation = list(method = "permutation_importance", important_factors = list("synthetic acuity"),
                         warning = "Non-causal explanation."),
      limitations = list("Synthetic-data prototype."),
      request = list(request_id = "REQ-1", review_mode = TRUE,
                     status = list("review_mode", "unapproved_model", "not_for_operational_use"))
    )
  )
  presented <- present_prediction(response)
  expect_true(presented$ok)
  expect_equal(presented$risk_band, "high")
  expect_match(presented$probability_label, "estimated")
})

test_that("malformed review-mode response is rejected", {
  bad <- list(
    prediction = list(long_stay_probability = 1.2),
    model = list(), explanation = list(), limitations = list(),
    request = list(review_mode = TRUE, status = list("review_mode"))
  )
  expect_error(validate_prediction_response(bad), "between 0 and 1")
})
