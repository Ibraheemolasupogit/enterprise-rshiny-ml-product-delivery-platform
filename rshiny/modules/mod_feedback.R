mod_feedback_ui <- function(id) {
  ns <- NS(id)
  tagList(
    tags$main(
      role = "main",
      h1("Synthetic product feedback"),
      p("Feedback is about the prototype experience only. Do not enter patient details."),
      sliderInput(ns("understandable_rating"), "Was the output understandable?", 1, 5, 4),
      sliderInput(ns("explanation_rating"), "Was the explanation useful?", 1, 5, 4),
      sliderInput(ns("usability_rating"), "Was the application easy to use?", 1, 5, 4),
      sliderInput(ns("governance_clarity_rating"), "Did the governance status appear clear?", 1, 5, 5),
      textAreaInput(ns("comment"), "Optional product comment. Do not include identifiers.", "", rows = 4),
      actionButton(ns("submit_feedback"), "Submit synthetic feedback"),
      uiOutput(ns("feedback_status"))
    )
  )
}

mod_feedback_server <- function(id, config, status) {
  moduleServer(id, function(input, output, session) {
    message <- reactiveVal(NULL)
    observeEvent(input$submit_feedback, {
      feedback <- list(
        understandable_rating = input$understandable_rating,
        explanation_rating = input$explanation_rating,
        usability_rating = input$usability_rating,
        governance_clarity_rating = input$governance_clarity_rating,
        comment = input$comment
      )
      tryCatch({
        api_submit_feedback(feedback, config, status())
        message("Feedback recorded locally for synthetic product evaluation.")
      }, error = function(err) {
        message(safe_error_message(err))
      })
    })
    output$feedback_status <- renderUI({
      req(message())
      tags$div(class = "feedback-status", `aria-live` = "polite", message())
    })
  })
}
