mod_batch_scoring_ui <- function(id) {
  ns <- NS(id)
  tagList(
    tags$main(
      role = "main",
      h1("Synthetic cohort scoring"),
      p("Upload a CSV of synthetic admission-time records only. Files are validated and not retained."),
      tags$section(
        class = "instructions",
        h2("CSV contract"),
        p("CSV files must use the sample template columns, contain no identifiers or outcomes, and include at most 100 rows."),
        downloadButton(ns("download_template"), "Download synthetic CSV template")
      ),
      fileInput(
        ns("cohort_file"),
        "Synthetic cohort CSV (required)",
        accept = c(".csv", "text/csv"),
        buttonLabel = "Choose CSV"
      ),
      actionButton(ns("validate_upload"), "Validate cohort"),
      actionButton(ns("score_batch"), "Score valid cohort", class = "btn-warning"),
      uiOutput(ns("validation_status")),
      tableOutput(ns("validation_table")),
      uiOutput(ns("batch_result_summary")),
      tableOutput(ns("batch_results")),
      downloadButton(ns("download_results"), "Download synthetic cohort predictions")
    )
  )
}

mod_batch_scoring_server <- function(id, config, client) {
  moduleServer(id, function(input, output, session) {
    uploaded <- reactiveVal(NULL)
    validation <- reactiveVal(NULL)
    batch_result <- reactiveVal(NULL)

    output$download_template <- downloadHandler(
      filename = function() "sample_cohort_template.csv",
      content = function(file) utils::write.csv(synthetic_template_records(), file, row.names = FALSE)
    )

    observeEvent(input$validate_upload, {
      req(input$cohort_file)
      result <- tryCatch({
        data <- read_batch_csv(input$cohort_file$datapath, config)
        table <- batch_validation_table(data)
        uploaded(data)
        validation(table)
        user_error("validation_error", sprintf(
          "Validation completed: %s valid rows and %s invalid rows.",
          sum(table$validation_status == "valid"),
          sum(table$validation_status != "valid")
        ))
      }, error = function(err) {
        uploaded(NULL)
        validation(data.frame(
          row_number = integer(), validation_status = character(),
          error_count = integer(), error_fields = character(), error_summary = character()
        ))
        user_error("validation_error", safe_error_message(err))
      })
      output$validation_status <- renderUI(error_panel(result))
    })

    observeEvent(input$score_batch, {
      req(uploaded())
      table <- validation()
      if (is.null(table) || any(table$validation_status != "valid")) {
        output$batch_result_summary <- renderUI(error_panel(user_error(
          "validation_error",
          "The cohort must pass validation before scoring."
        )))
        return()
      }
      records <- tryCatch(batch_records_from_dataframe(uploaded()), error = identity)
      if (inherits(records, "error")) {
        output$batch_result_summary <- renderUI(error_panel(user_error(
          "validation_error",
          safe_error_message(records)
        )))
        return()
      }
      response <- api_predict_batch(client, records, config)
      presented <- tryCatch(
        present_batch_predictions(response, records),
        error = function(err) list(ok = FALSE, message = safe_error_message(err), code = "malformed_response")
      )
      batch_result(presented)
    })

    output$validation_table <- renderTable({
      req(validation())
      validation()
    }, striped = TRUE, spacing = "s")

    output$batch_result_summary <- renderUI({
      result <- batch_result()
      if (is.null(result)) return(NULL)
      if (!isTRUE(result$ok)) {
        return(error_panel(user_error(result$code %||% "unexpected_error", result$message)))
      }
      summary <- result$summary
      tags$section(
        class = "prediction-result",
        role = "status",
        h2("Cohort result summary"),
        p(class = "warning-text", synthetic_results_statement),
        tags$dl(
          tags$dt("Records scored"), tags$dd(summary$records_scored),
          tags$dt("High-risk count"), tags$dd(summary$high_risk_count),
          tags$dt("Predicted positive count"), tags$dd(summary$predicted_positive_count),
          tags$dt("Mean probability"), tags$dd(sprintf("%.3f", summary$mean_probability)),
          tags$dt("Median probability"), tags$dd(sprintf("%.3f", summary$median_probability)),
          tags$dt("Probability range"), tags$dd(sprintf("%.3f to %.3f", summary$min_probability, summary$max_probability))
        )
      )
    })

    output$batch_results <- renderTable({
      result <- batch_result()
      req(result, isTRUE(result$ok))
      result$results[batch_result_fields]
    }, striped = TRUE, spacing = "s")

    output$download_results <- downloadHandler(
      filename = function() safe_export_filename(),
      content = function(file) {
        result <- batch_result()
        req(result, isTRUE(result$ok))
        write_export_csv(result$results, file)
      }
    )
  })
}
