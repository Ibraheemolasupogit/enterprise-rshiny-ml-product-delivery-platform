library(shinytest2)

test_that("advanced app exposes Milestone 12 read-only retraining page", {
  skip_if_not_installed("shinytest2")
  app_dir <- normalizePath(file.path("..", ".."), mustWork = TRUE)
  app <- AppDriver$new(name = "rshiny-advanced", app_dir = app_dir, load_timeout = 10000)
  expect_true(length(app$get_value(output = "status_banner-banner")) >= 0)
  app$click(selector = "a[data-value='Retraining Review']")
  app$wait_for_js(
    "document.body.innerText.includes('This page displays retraining evidence only')"
  )
  body_text <- app$get_js("document.body.innerText")
  expect_match(body_text, "Overview")
  expect_match(body_text, "Cohort Scoring")
  expect_match(body_text, "Model Performance")
  expect_match(body_text, "Model Governance")
  expect_match(body_text, "Monitoring")
  expect_match(body_text, "Retraining Review")
  expect_match(body_text, "This page displays retraining evidence only")
  expect_false(grepl("Run retraining|Register challenger|Approve challenger", body_text))
  expect_match(body_text, "LOCAL REVIEW MODE|SCORING UNAVAILABLE")
})
