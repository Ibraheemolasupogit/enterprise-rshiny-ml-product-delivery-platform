mod_retraining_review_ui <- function(id) {
  ns <- NS(id)
  tagList(
    tags$main(
      role = "main",
      h1("Retraining Review"),
      p("This page displays retraining evidence only."),
      p("It cannot retrain, register, approve, activate or deploy a model."),
      uiOutput(ns("status")),
      h2("Eligibility"),
      tableOutput(ns("eligibility")),
      h2("Dataset"),
      tableOutput(ns("dataset")),
      h2("Champion"),
      tableOutput(ns("champion")),
      h2("Challengers"),
      tableOutput(ns("challengers")),
      h2("Comparison"),
      tableOutput(ns("comparison")),
      h2("Gates"),
      tableOutput(ns("gates")),
      h2("Recommendation"),
      tableOutput(ns("recommendation"))
    )
  )
}

mod_retraining_review_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    evidence <- reactive({
      tryCatch(load_retraining_evidence(), error = function(err) err)
    })

    output$status <- renderUI({
      current <- evidence()
      if (inherits(current, "error")) {
        return(error_panel(user_error("evidence_unavailable", safe_error_message(current))))
      }
      tags$div(class = "feedback-status", "Retraining review evidence loaded. Automatic action is none.")
    })

    output$eligibility <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      retraining_status_table(current)
    }, striped = TRUE, spacing = "s")

    output$dataset <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      data.frame(
        field = c("Eligible rows", "Excluded rows", "Train rows", "Validation rows",
                  "Patient overlap", "Admission overlap"),
        value = c(
          current$dataset$eligible_rows,
          current$dataset$excluded_rows,
          current$split$train_rows,
          current$split$validation_rows,
          current$split$patient_overlap_count,
          current$split$admission_overlap_count
        )
      )
    }, striped = TRUE, spacing = "s")

    output$champion <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      data.frame(
        field = c("Model", "Registry version", "Candidate", "Calibration", "Threshold",
                  "Registry state", "Approval", "Activation"),
        value = c(
          current$champion$model_name,
          current$champion$registry_version,
          current$champion$candidate_identifier,
          current$champion$calibration,
          current$champion$threshold,
          current$champion$registry_state,
          current$champion$approval_state,
          current$champion$activation_state
        )
      )
    }, striped = TRUE, spacing = "s")

    output$challengers <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      retraining_challenger_table(current)
    }, striped = TRUE, spacing = "s", digits = 3)

    output$comparison <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      best <- current$comparison$best_challenger_candidate_identifier
      row <- Filter(function(item) identical(item$candidate_identifier, best), current$comparison$challengers)[[1]]
      data.frame(
        metric = c("PR-AUC delta", "ROC-AUC delta", "Brier delta", "Recall delta",
                   "Specificity delta", "Balanced accuracy delta", "Weighted cost delta"),
        value = c(
          row$challenger_minus_champion_pr_auc,
          row$challenger_minus_champion_roc_auc,
          row$challenger_minus_champion_brier,
          row$challenger_minus_champion_recall,
          row$challenger_minus_champion_specificity,
          row$challenger_minus_champion_balanced_accuracy,
          row$challenger_minus_champion_weighted_cost
        )
      )
    }, striped = TRUE, spacing = "s", digits = 3)

    output$gates <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      retraining_gate_table(current)
    }, striped = TRUE, spacing = "s")

    output$recommendation <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      data.frame(
        field = c("Recommendation", "Human review required", "Automatic action",
                  "Approval", "Activation", "Deployment"),
        value = c(
          current$recommendation$recommendation,
          current$recommendation$human_review_required,
          current$recommendation$automatic_action,
          current$recommendation$approval_status,
          current$recommendation$activation_status,
          current$recommendation$deployment_status
        )
      )
    }, striped = TRUE, spacing = "s")
  })
}
