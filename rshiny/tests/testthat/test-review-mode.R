test_that("review banner status derives from API readiness", {
  status <- list(
    ready = list(ok = TRUE, data = list(review_mode = TRUE)),
    model = list(ok = TRUE, data = list(available = TRUE))
  )
  expect_true(is_review_mode(status))
  expect_match(status_text(status), "LOCAL REVIEW MODE")
})

test_that("unavailable banner appears when no model is ready", {
  status <- list(
    ready = list(ok = TRUE, data = list(review_mode = FALSE, ready = FALSE)),
    model = list(ok = FALSE, data = list())
  )
  expect_false(is_review_mode(status))
  expect_match(status_text(status), "SCORING UNAVAILABLE")
})
