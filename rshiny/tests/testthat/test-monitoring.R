test_that("monitoring evidence is loaded and validated", {
  evidence <- load_monitoring_evidence()
  expect_equal(evidence$review$registry_mutation_status, "none")
  expect_equal(evidence$review$model_replacement_status, "none")
  expect_equal(evidence$summary$automatic_action, "none")
  expect_true(length(evidence$alerts$alerts) > 0)
})

test_that("monitoring presenters keep drift and performance distinct", {
  evidence <- load_monitoring_evidence()
  status <- monitoring_status_table(evidence)
  alerts <- monitoring_alert_table(evidence)
  expect_true("Monitoring run" %in% status$field)
  expect_true("Disposition" %in% status$field)
  expect_true("automatic_action" %in% names(alerts))
  expect_true(all(alerts$automatic_action %in% c("none", "human_review_required")))
  expect_true(isTRUE(evidence$performance$labels_available))
})

test_that("monitoring module contains no mutation controls", {
  module_text <- paste(readLines(file.path(app_root, "modules", "mod_monitoring.R")), collapse = "\n")
  forbidden <- c("actionButton", "Retrain", "Promote", "Activate", "Approve", "Deploy", "Rollback")
  for (pattern in forbidden) {
    expect_false(grepl(pattern, module_text, fixed = TRUE), info = pattern)
  }
})
