test_that("batch contract has stable required columns", {
  contract <- batch_contract()
  expect_equal(contract$required_columns, prediction_fields)
  expect_equal(contract$maximum_rows, 100)
  expect_true("patient_id" %in% contract$prohibited_columns)
  expect_equal(unlist(contract$accepted_formats), "csv")
})

test_that("batch dataframe rejects schema drift", {
  data <- synthetic_template_records()
  expect_silent(validate_batch_dataframe(data))
  expect_error(validate_batch_dataframe(data[setdiff(names(data), "age")]), "missing")
  extra <- data
  extra$unexpected <- "x"
  expect_error(validate_batch_dataframe(extra), "unsupported")
  prohibited <- data
  prohibited$patient_id <- "P1"
  expect_error(validate_batch_dataframe(prohibited), "prohibited")
})

test_that("batch dataframe rejects invalid row values", {
  data <- synthetic_template_records()
  data$sex[1] <- "unknown"
  table <- batch_validation_table(data)
  expect_equal(table$validation_status[1], "invalid")
  data <- synthetic_template_records()
  data$age[1] <- 111
  expect_equal(batch_validation_table(data)$validation_status[1], "invalid")
  data <- synthetic_template_records()
  data$admission_datetime[1] <- "not-a-date"
  expect_equal(batch_validation_table(data)$validation_status[1], "invalid")
})

test_that("batch row limit is enforced", {
  data <- synthetic_template_records()
  too_many <- data[rep(seq_len(nrow(data)), 51), ]
  expect_error(validate_batch_dataframe(too_many), "row limit")
})

test_that("batch response validates order, labels and registry consistency", {
  records <- batch_records_from_dataframe(synthetic_template_records())
  response_item <- function(record, version = 1) {
    list(
      prediction = list(long_stay_probability = 0.8, predicted_long_stay = TRUE, risk_band = "high"),
      model = list(model_name = "long_stay_admission_risk", registry_version = version,
                   candidate_identifier = "CAND-85EA9202CAD6FE7F", model_family = "xgboost",
                   calibration = "sigmoid", threshold = 0.75, approval_status = "pending",
                   activation_status = "inactive"),
      explanation = list(method = "permutation_importance", important_factors = list("synthetic acuity"),
                         warning = "Non-causal explanation."),
      limitations = list("Synthetic-data prototype."),
      request = list(request_id = record$request_id, review_mode = TRUE,
                     status = list("review_mode", "unapproved_model", "not_for_operational_use"))
    )
  }
  data <- list(response_item(records[[1]]), response_item(records[[2]]))
  expect_silent(validate_batch_response(data, records))
  bad_order <- data
  bad_order[[1]]$request$request_id <- records[[2]]$request_id
  expect_error(validate_batch_response(bad_order, records), "order")
  bad_version <- data
  bad_version[[2]] <- response_item(records[[2]], version = 2)
  expect_error(validate_batch_response(bad_version, records), "inconsistent")
  bad_labels <- data
  bad_labels[[1]]$request$status <- list("review_mode")
  expect_error(validate_batch_response(bad_labels, records), "Review-mode")
})
