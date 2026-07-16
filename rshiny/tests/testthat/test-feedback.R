test_that("feedback validates ranges and writes JSONL", {
  cfg <- load_app_config()
  tmp <- tempfile(fileext = ".jsonl")
  cfg$feedback$output_path <- file.path("data", "monitoring", basename(tmp))
  feedback <- list(
    understandable_rating = 5,
    explanation_rating = 4,
    usability_rating = 4,
    governance_clarity_rating = 5,
    comment = "Synthetic product feedback only"
  )
  expect_true(validate_feedback(feedback))
})

test_that("feedback rejects unsafe content shape", {
  feedback <- list(
    understandable_rating = 6,
    explanation_rating = 4,
    usability_rating = 4,
    governance_clarity_rating = 5,
    comment = ""
  )
  expect_error(validate_feedback(feedback), "between 1 and 5")
})
