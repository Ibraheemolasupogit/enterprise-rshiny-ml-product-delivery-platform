test_that("performance and governance evidence validates locked state", {
  evidence <- load_model_evidence()
  summary <- performance_summary(evidence)
  expect_equal(summary$recommended_model, "xgboost")
  expect_equal(summary$approval_status, "pending")
  expect_equal(summary$activation_status, "inactive")
  expect_equal(round(summary$test$specificity, 3), 0.4)
  expect_equal(round(summary$test$balanced_accuracy, 3), 0.561)
})

test_that("governance evidence remains read only and pending", {
  evidence <- load_model_evidence()
  summary <- governance_summary(evidence)
  expect_equal(summary$state$registry_state, "registered")
  expect_equal(summary$state$approval_status, "pending")
  expect_equal(summary$state$activation_status, "inactive")
  expect_equal(summary$state$governance_recommendation, "defer")
  flag_codes <- vapply(summary$flags, function(flag) flag$code, character(1))
  expect_true("weak_test_specificity" %in% flag_codes)
  expect_true("fairness_groups_suppressed" %in% flag_codes)
})

test_that("governance module does not expose mutation controls", {
  html <- paste(as.character(mod_governance_ui("gov")), collapse = " ")
  prohibited <- c("Approve", "Reject", "Activate", "Retire", "Roll back", "Register", "Deploy")
  for (label in prohibited) {
    expect_false(grepl(label, html, fixed = TRUE), info = label)
  }
})
