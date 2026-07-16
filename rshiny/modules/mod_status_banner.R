mod_status_banner_ui <- function(id) {
  ns <- NS(id)
  uiOutput(ns("banner"))
}

mod_status_banner_server <- function(id, status) {
  moduleServer(id, function(input, output, session) {
    output$banner <- renderUI({
      current <- status()
      tags$section(
        class = review_mode_status_class(current),
        role = "status",
        `aria-live` = "polite",
        tags$strong(if (is_review_mode(current)) "LOCAL REVIEW MODE" else "SCORING UNAVAILABLE"),
        tags$p(status_text(current)),
        tags$ul(lapply(review_mode_labels, tags$li))
      )
    })
  })
}
