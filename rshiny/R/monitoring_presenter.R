monitoring_status_table <- function(evidence) {
  data.frame(
    field = c(
      "Monitoring run", "Baseline", "Window type", "Window rows",
      "Labels available", "Disposition", "Warnings", "Critical alerts",
      "Automatic action", "Human review"
    ),
    value = c(
      evidence$run$monitoring_run_identifier,
      evidence$run$baseline_identifier,
      "current labelled monitoring window",
      evidence$run$window_row_count,
      evidence$run$label_availability,
      evidence$review$overall_disposition,
      evidence$alerts$warning_count,
      evidence$alerts$critical_count,
      "none",
      evidence$alerts$requires_review_count
    ),
    stringsAsFactors = FALSE
  )
}
monitoring_alert_table <- function(evidence) {
  alerts <- evidence$alerts$alerts
  if (length(alerts) == 0) {
    return(data.frame(message = "No monitoring alerts.", stringsAsFactors = FALSE))
  }
  data.frame(
    severity = vapply(alerts, function(alert) alert$severity, character(1)),
    category = vapply(alerts, function(alert) alert$category, character(1)),
    metric = vapply(alerts, function(alert) alert$metric, character(1)),
    reason = vapply(alerts, function(alert) alert$reason, character(1)),
    requires_review = vapply(alerts, function(alert) as.character(alert$requires_review), character(1)),
    automatic_action = vapply(alerts, function(alert) alert$automatic_action, character(1)),
    stringsAsFactors = FALSE
  )
}
