test_that("export dataframe contains only safe fields", {
  results <- data.frame(
    row_number = 1:2,
    long_stay_probability = c(0.8, 0.3),
    predicted_long_stay = c(TRUE, FALSE),
    risk_band = c("high", "low"),
    model_registry_version = c(1, 1),
    model_family = c("xgboost", "xgboost"),
    candidate_identifier = c("CAND-85EA9202CAD6FE7F", "CAND-85EA9202CAD6FE7F"),
    threshold = c(0.75, 0.75),
    review_mode = c(TRUE, TRUE)
  )
  exported <- build_export_dataframe(results, as.POSIXct("2026-07-15 12:00:00", tz = "UTC"))
  expect_equal(names(exported), batch_export_fields)
  expect_true(all(exported$synthetic_data_statement == synthetic_results_statement))
  expect_false(any(grepl("API|models/|data/processed|patient_id|long_stay_flag", names(exported))))
  expect_match(safe_export_filename(as.POSIXct("2026-07-15 12:00:00", tz = "UTC")),
               "^synthetic_cohort_predictions_20260715T120000Z[.]csv$")
})
