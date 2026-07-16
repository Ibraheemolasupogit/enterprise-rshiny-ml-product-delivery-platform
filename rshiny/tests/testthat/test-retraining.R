test_that("retraining evidence is loaded and validated", {
  evidence <- load_retraining_evidence()
  expect_equal(evidence$recommendation$automatic_action, "none")
  expect_equal(evidence$recommendation$approval_status, "not_granted")
  expect_equal(evidence$recommendation$activation_status, "inactive")
  expect_equal(evidence$recommendation$deployment_status, "not_performed")
  expect_true(evidence$recommendation$human_review_required)
})

test_that("retraining evidence keeps champion and challenger identities visible", {
  evidence <- load_retraining_evidence()
  status <- retraining_status_table(evidence)
  challengers <- retraining_challenger_table(evidence)
  expect_true("Recommendation" %in% status$field)
  expect_equal(evidence$champion$candidate_identifier, "CAND-85EA9202CAD6FE7F")
  expect_true(nrow(challengers) >= 3)
  expect_true(all(challengers$reproducible == "TRUE"))
})

test_that("retraining comparison preserves metric directions and gate meaning", {
  evidence <- load_retraining_evidence()
  first <- evidence$comparison$challengers[[1]]
  expect_equal(first$metric_directions$pr_auc, "higher_is_better")
  expect_equal(first$metric_directions$brier_score, "lower_is_better")
  expect_true(evidence$gates$approval_not_implied)
  expect_true(evidence$gates$overall_result %in% c("pass", "conditional", "fail", "insufficient_evidence"))
})

test_that("retraining module contains no execution or registry mutation controls", {
  module_text <- paste(readLines(file.path(app_root, "modules", "mod_retraining_review.R")), collapse = "\n")
  forbidden <- c("actionButton", "downloadButton", "Run retraining", "Register challenger")
  for (pattern in forbidden) {
    expect_false(grepl(pattern, module_text, fixed = TRUE), info = pattern)
  }
})
