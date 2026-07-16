mod_governance_ui <- function(id) {
  ns <- NS(id)
  tagList(
    tags$main(
      role = "main",
      h1("Model governance"),
      p("Read-only registry and governance evidence for the registered synthetic candidate."),
      uiOutput(ns("governance_status")),
      h2("Registry identity"),
      tableOutput(ns("identity_table")),
      h2("State"),
      tableOutput(ns("state_table")),
      h2("Governance review"),
      uiOutput(ns("review_flags")),
      h2("Approval"),
      tableOutput(ns("approval_table")),
      h2("Audit summary"),
      tableOutput(ns("audit_table")),
      h2("Model-card summary"),
      uiOutput(ns("model_card_summary"))
    )
  )
}

mod_governance_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    evidence <- reactive({
      tryCatch(load_model_evidence(), error = function(err) err)
    })

    output$governance_status <- renderUI({
      current <- evidence()
      if (inherits(current, "error")) {
        return(error_panel(user_error("evidence_unavailable", safe_error_message(current))))
      }
      tags$div(
        class = "feedback-status",
        `aria-live` = "polite",
        "Governance view is read-only. Approval is pending, activation is inactive, and the recommendation is defer."
      )
    })

    output$identity_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      identity <- governance_summary(current)$identity
      data.frame(field = names(identity), value = unlist(identity), row.names = NULL)
    }, striped = TRUE, spacing = "s")

    output$state_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      state <- governance_summary(current)$state
      data.frame(field = names(state), value = unlist(state), row.names = NULL)
    }, striped = TRUE, spacing = "s")

    output$review_flags <- renderUI({
      current <- evidence()
      req(!inherits(current, "error"))
      summary <- governance_summary(current)
      tags$div(
        h3("Hard requirements"),
        tags$ul(lapply(names(summary$hard_requirements), function(name) {
          tags$li(paste(name, summary$hard_requirements[[name]]))
        })),
        h3("Review flags"),
        tags$ul(lapply(summary$flags, function(flag) {
          tags$li(paste(flag$code, "-", flag$detail))
        })),
        p("Weak test specificity, validation-to-test degradation, small sample size, suppressed fairness groups, synthetic-only evidence and native dependency requirements are disclosed.")
      )
    })

    output$approval_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      approval <- governance_summary(current)$approval
      data.frame(
        field = c("Automatic approval", "Human decision required", "Current approval decision"),
        value = c("disabled", if (isTRUE(approval$human_decision_required)) "yes" else "no",
                  approval$current_decision)
      )
    }, striped = TRUE, spacing = "s")

    output$audit_table <- renderTable({
      current <- evidence()
      req(!inherits(current, "error"))
      events <- safe_audit_events(current)
      data.frame(
        timestamp_utc = vapply(events, function(event) event$timestamp_utc, character(1)),
        event_type = vapply(events, function(event) event$event_type, character(1)),
        actor = vapply(events, function(event) event$actor, character(1)),
        registry_version = vapply(events, function(event) as.character(event$registry_version), character(1)),
        stringsAsFactors = FALSE
      )
    }, striped = TRUE, spacing = "s")

    output$model_card_summary <- renderUI({
      current <- evidence()
      req(!inherits(current, "error"))
      tags$ul(lapply(model_card_summary(current), tags$li))
    })
  })
}
