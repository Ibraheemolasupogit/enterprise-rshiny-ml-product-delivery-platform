library(shiny)
library(bslib)

global_path <- if (file.exists("global.R")) "global.R" else file.path("rshiny", "global.R")
source(global_path, local = TRUE)
app_config <- load_app_config()

ui <- page_navbar(
  title = app_config$application$title,
  theme = bs_theme(version = 5, bootswatch = "flatly"),
  header = tagList(
    includeCSS(file.path(shiny_app_root, "www", "app.css")),
    tags$a(class = "skip-link", href = "#main-content", "Skip to main content"),
    mod_status_banner_ui("status_banner")
  ),
  nav_panel("Overview", mod_overview_ui("overview")),
  nav_panel("Single Prediction", mod_prediction_ui("prediction")),
  nav_panel("Cohort Scoring", mod_batch_scoring_ui("batch")),
  nav_panel("Model Performance", mod_performance_ui("performance")),
  nav_panel("Monitoring", mod_monitoring_ui("monitoring")),
  nav_panel("Retraining Review", mod_retraining_review_ui("retraining")),
  nav_panel("Model Governance", mod_governance_ui("governance")),
  nav_panel("Feedback", mod_feedback_ui("feedback"))
)

server <- function(input, output, session) {
  cfg <- load_app_config()
  client <- api_client_from_env(cfg)
  status <- reactiveVal(fetch_service_status(client))

  mod_status_banner_server("status_banner", status)
  mod_overview_server("overview", cfg, status)
  mod_prediction_server("prediction", cfg, client, status)
  mod_batch_scoring_server("batch", cfg, client)
  mod_performance_server("performance")
  mod_monitoring_server("monitoring")
  mod_retraining_review_server("retraining")
  mod_governance_server("governance")
  mod_feedback_server("feedback", cfg, status)
}

shinyApp(ui, server)
