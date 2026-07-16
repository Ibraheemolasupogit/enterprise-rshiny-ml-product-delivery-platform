mod_overview_ui <- function(id) {
  ns <- NS(id)
  tagList(
    tags$main(
      id = "main-content",
      role = "main",
      h1("Synthetic long-stay decision-support prototype"),
      p("This MVP demonstrates a governed R-Shiny client for a local FastAPI scoring service."),
      uiOutput(ns("overview_status")),
      h2("Product boundary"),
      tags$ul(
        tags$li("Intended users: product, analytics and operational review stakeholders."),
        tags$li("Decision-support only; it does not provide clinical recommendations."),
        tags$li("Synthetic-data prototype only."),
        tags$li("Prediction point: admission-time operational context."),
        tags$li("Target: synthetic long stay above the configured threshold.")
      ),
      h2("Important current state"),
      tags$p(class = "warning-text",
             "The registered model is not approved or active. Default operational scoring is unavailable. Local review mode is for technical demonstration only.")
    )
  )
}

mod_overview_server <- function(id, config, status) {
  moduleServer(id, function(input, output, session) {
    output$overview_status <- renderUI({
      current <- status()
      model <- current$model$data %||% list()
      ready <- current$ready$data %||% list()
      tags$dl(
        tags$dt("Current model family"), tags$dd(model$model_family %||% "XGBoost"),
        tags$dt("Registry version"), tags$dd(model$registry_version %||% "1"),
        tags$dt("Candidate identifier"), tags$dd(model$candidate_identifier %||% "CAND-85EA9202CAD6FE7F"),
        tags$dt("Approval status"), tags$dd(model$approval_status %||% "pending"),
        tags$dt("Activation status"), tags$dd(model$activation_status %||% "inactive"),
        tags$dt("API readiness"), tags$dd(if (isTRUE(ready$ready)) "ready in review mode" else "not ready for operational scoring"),
        tags$dt("Review-mode status"), tags$dd(if (isTRUE(ready$review_mode)) "enabled" else "disabled"),
        tags$dt("Last evidence version"), tags$dd("MODEL-REG-000001")
      )
    })
  })
}
