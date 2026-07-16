mod_monitoring_ui <- function(id) {
  ns <- NS(id)
  tagList(
    tags$main(
      role = "main",
      h1("Monitoring"),
      p("Read-only synthetic monitoring evidence. Drift triggers review, not retraining."),
      uiOutput(ns("monitoring_status")),
      h2("Current monitoring status"),
      tableOutput(ns("status_table")),
      h2("Data quality"),
      tableOutput(ns("data_quality_table")),
      h2("Feature drift"),
      tableOutput(ns("feature_drift_table")),
      h2("Prediction drift"),
      uiOutput(ns("prediction_warning")),
      tableOutput(ns("prediction_table")),
      h2("Performance"),
      uiOutput(ns("performance_boundary")),
      tableOutput(ns("performance_table")),
      h2("Operational metrics"),
      tableOutput(ns("operational_table")),
      h2("Alerts"),
      tableOutput(ns("alerts_table")),
      h2("Next-step guidance"),
      uiOutput(ns("next_steps"))
    )
  )
}

mod_monitoring_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    evidence <- reactive({
      tryCatch(load_monitoring_evidence(), error = function(err) err)
    })

    output$monitoring_status <- renderUI({
      current <- evidence()
      if (inherits(current, "error")) {
        return(error_panel(user_error("evidence_unavailable", safe_error_message(current))))
      }
      tags$div(
        class = "feedback-status",
        `aria-live` = "polite",
        "Monitoring evidence loaded. Automatic action is none; human review may be required."
      )
    })

    output$status_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      monitoring_status_table(current)
    }, striped = TRUE, spacing = "s")

    output$data_quality_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      data.frame(
        metric = c("Schema", "Missingness", "Invalid values", "Critical affected fields"),
        value = c(
          current$schema$status,
          current$missingness$status,
          current$data_quality$invalid_value_status,
          paste(current$data_quality$critical_affected_fields, collapse = ", ")
        )
      )
    }, striped = TRUE, spacing = "s")

    output$feature_drift_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      data.frame(
        metric = c("Numeric status", "Categorical status", "Numeric warnings", "Numeric critical",
                   "Categorical warnings", "Categorical critical"),
        value = c(
          current$numeric$status,
          current$categorical$status,
          paste(current$numeric$warning_features, collapse = ", "),
          paste(current$numeric$critical_features, collapse = ", "),
          paste(current$categorical$warning_features, collapse = ", "),
          paste(current$categorical$critical_features, collapse = ", ")
        )
      )
    }, striped = TRUE, spacing = "s")

    output$prediction_warning <- renderUI({
      tags$p(class = "warning-text", "Prediction drift is not performance drift without outcome labels.")
    })

    output$prediction_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      data.frame(
        metric = c("Probability PSI", "Mean probability change", "Positive-rate change", "Status"),
        value = c(
          current$prediction$probability_psi,
          current$prediction$mean_probability_change,
          current$prediction$positive_rate_change,
          current$prediction$status
        )
      )
    }, striped = TRUE, spacing = "s", digits = 3)

    output$performance_boundary <- renderUI({
      tags$p("Performance monitoring requires outcome labels. Threshold and calibration are unchanged.")
    })

    output$performance_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      if (!isTRUE(current$performance$labels_available)) {
        return(data.frame(message = "Performance monitoring unavailable because outcomes are not present."))
      }
      metrics <- current$performance$metrics
      data.frame(
        metric = c("PR-AUC", "ROC-AUC", "Recall", "Specificity", "Brier", "Status"),
        value = c(metrics$pr_auc, metrics$roc_auc, metrics$recall, metrics$specificity,
                  metrics$brier_score, current$performance$status)
      )
    }, striped = TRUE, spacing = "s", digits = 3)

    output$operational_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      data.frame(
        metric = c("Events", "Success", "Error rate", "Median latency", "P95 latency",
                   "Review-mode events", "Unknown-version events", "Status"),
        value = c(
          current$operational$event_count,
          current$operational$success_count,
          current$operational$error_rate,
          current$operational$median_latency_ms,
          current$operational$p95_latency_ms,
          current$operational$review_mode_event_count,
          current$operational$unknown_version_events,
          current$operational$status
        )
      )
    }, striped = TRUE, spacing = "s")

    output$alerts_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      monitoring_alert_table(current)
    }, striped = TRUE, spacing = "s")

    output$next_steps <- renderUI({
      current <- evidence()
      req(!inherits(current, "error"))
      tags$ul(lapply(current$review$suggested_next_steps, tags$li))
    })
  })
}
