review_mode_labels <- c(
  "Review mode",
  "Unapproved model",
  "Synthetic-data prototype",
  "Not for operational or clinical use"
)

is_review_mode <- function(status) {
  ready <- status$ready
  isTRUE(ready$ok) && isTRUE(ready$data$review_mode)
}

review_mode_status_class <- function(status) {
  if (is_review_mode(status)) {
    "status-banner status-banner-review"
  } else {
    "status-banner status-banner-unavailable"
  }
}
