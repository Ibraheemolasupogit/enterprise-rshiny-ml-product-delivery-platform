mod_performance_ui <- function(id) {
  ns <- NS(id)
  tagList(
    tags$main(
      role = "main",
      h1("Model performance"),
      p("This page reads committed model-evaluation evidence only. It does not recalculate live metrics."),
      uiOutput(ns("performance_status")),
      h2("Recommendation"),
      tableOutput(ns("recommendation_table")),
      h2("Validation comparison"),
      tableOutput(ns("comparison_table")),
      h2("Locked test results"),
      tableOutput(ns("test_table")),
      h2("Validation-to-test degradation"),
      tableOutput(ns("degradation_table")),
      h2("Limitations"),
      uiOutput(ns("limitations"))
    )
  )
}

mod_performance_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    evidence <- reactive({
      tryCatch(load_model_evidence(), error = function(err) err)
    })

    output$performance_status <- renderUI({
      current <- evidence()
      if (inherits(current, "error")) {
        return(error_panel(user_error("evidence_unavailable", safe_error_message(current))))
      }
      tags$div(
        class = "feedback-status",
        `aria-live` = "polite",
        "Evidence loaded from committed model-evaluation files. Test specificity 0.400 and balanced accuracy 0.561 remain visible."
      )
    })

    output$recommendation_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      summary <- performance_summary(current)
      data.frame(
        field = c("Recommended model", "Calibration", "Selected threshold",
                  "Approval status", "Activation status"),
        value = c(summary$recommended_model, summary$calibration, summary$selected_threshold,
                  summary$approval_status, summary$activation_status)
      )
    }, striped = TRUE, spacing = "s")

    output$comparison_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      metrics_table(current$model_comparison$rows)
    }, striped = TRUE, spacing = "s", digits = 3)

    output$test_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      metrics <- current$test_metrics$metrics
      data.frame(
        metric = c("PR-AUC", "ROC-AUC", "Brier", "Log loss", "Precision",
                   "Recall", "Specificity", "F1", "Balanced accuracy",
                   "True positives", "False positives", "True negatives", "False negatives"),
        value = c(metrics$pr_auc, metrics$roc_auc, metrics$brier_score, metrics$log_loss,
                  metrics$precision, metrics$recall, metrics$specificity, metrics$f1,
                  metrics$balanced_accuracy, metrics$confusion_matrix$true_positives,
                  metrics$confusion_matrix$false_positives, metrics$confusion_matrix$true_negatives,
                  metrics$confusion_matrix$false_negatives)
      )
    }, striped = TRUE, spacing = "s", digits = 3)

    output$degradation_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      degradation <- performance_summary(current)$degradation
      data.frame(metric = names(degradation), validation_minus_test = unlist(degradation))
    }, striped = TRUE, spacing = "s", digits = 3)

    output$limitations <- renderUI({
      tags$ul(
        tags$li("Synthetic data only; metrics are not clinically validated."),
        tags$li("Small locked test set with high positive prevalence."),
        tags$li("Subgroup fairness estimates are exploratory and suppressed when too small."),
        tags$li("The candidate is registered for review, not approved or active."),
        tags$li("No monitoring, drift detection or live recalculation is performed here.")
      )
    })
  })
}
