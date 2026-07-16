test_that("prediction contract excludes identifiers and outcomes", {
  expect_false(any(c("patient_id", "admission_id", "long_stay_flag") %in% prediction_fields))
  expect_true(all(c("age", "sex", "admission_datetime") %in% prediction_fields))
})

test_that("synthetic example validates and builds API payload", {
  payload <- build_prediction_payload(synthetic_example_record())
  expect_equal(length(payload), length(prediction_fields))
  expect_named(payload, prediction_fields)
})

test_that("invalid categorical and numeric inputs are rejected", {
  record <- synthetic_example_record()
  record$sex <- "unknown"
  expect_error(validate_prediction_record(record), "unsupported")
  record <- synthetic_example_record()
  record$age <- 7
  expect_error(validate_prediction_record(record), "outside")
  record <- synthetic_example_record()
  record$patient_id <- "P1"
  expect_error(validate_prediction_record(record), "Prohibited")
})
