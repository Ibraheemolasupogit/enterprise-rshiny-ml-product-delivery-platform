mod_prediction_ui <- function(id) {
  ns <- NS(id)
  tagList(
    tags$main(
      role = "main",
      h1("Single synthetic prediction"),
      p("Enter synthetic admission-time values only. Do not enter real patient data."),
      actionButton(ns("load_example"), "Load synthetic example"),
      actionButton(ns("reset"), "Reset form"),
      tags$form(
        class = "prediction-form",
        numericInput(ns("age"), "Age in years (required)", 78, min = 18, max = 110),
        selectInput(ns("sex"), "Sex (required)", allowed_values$sex),
        selectInput(ns("postcode_region"), "Synthetic postcode region (required)", allowed_values$postcode_region),
        numericInput(ns("deprivation_decile"), "Deprivation decile, 1 to 10 (required)", 4, min = 1, max = 10),
        numericInput(ns("comorbidity_count"), "Comorbidity count (required)", 3, min = 0),
        numericInput(ns("previous_admissions_12m"), "Previous admissions in 12 months (required)", 2, min = 0),
        selectInput(ns("admission_type"), "Admission type (required)", allowed_values$admission_type),
        selectInput(ns("source_of_admission"), "Source of admission (required)", allowed_values$source_of_admission),
        numericInput(ns("initial_news2_score"), "Initial NEWS2 score, synthetic (required)", 7, min = 0, max = 20),
        selectInput(ns("mobility_status"), "Mobility status (required)", allowed_values$mobility_status),
        selectInput(ns("primary_diagnosis_group"), "Synthetic primary diagnosis group (required)", allowed_values$primary_diagnosis_group),
        selectInput(ns("primary_diagnosis_complexity"), "Synthetic diagnosis complexity (required)", allowed_values$primary_diagnosis_complexity),
        numericInput(ns("diagnosis_count"), "Diagnosis count (required)", 4, min = 1),
        numericInput(ns("secondary_diagnosis_count"), "Secondary diagnosis count (required)", 2, min = 0),
        numericInput(ns("staffed_beds"), "Staffed beds (required)", 36, min = 1),
        numericInput(ns("occupied_beds"), "Occupied beds (required)", 32, min = 0),
        numericInput(ns("closed_beds"), "Closed beds (required)", 2, min = 0),
        numericInput(ns("isolation_capacity"), "Isolation capacity (required)", 4, min = 0),
        numericInput(ns("registered_nurses"), "Registered nurses on shift (required)", 9, min = 0),
        numericInput(ns("support_workers"), "Support workers on shift (required)", 11, min = 0),
        numericInput(ns("medical_staff"), "Medical staff on shift (required)", 5, min = 0),
        numericInput(ns("agency_hours"), "Agency hours (required)", 12, min = 0),
        numericInput(ns("vacancy_rate"), "Vacancy rate, 0 to 1 (required)", 0.08, min = 0, max = 1, step = 0.01),
        numericInput(ns("occupancy_rate"), "Occupancy rate, optional 0 to 1.5", 0.89, min = 0, max = 1.5, step = 0.01),
        numericInput(ns("staff_to_bed_ratio"), "Staff to bed ratio, optional", 0.69, min = 0, step = 0.01),
        textInput(ns("admission_datetime"), "Admission datetime UTC, ISO-8601 (required)", "2026-07-15T09:30:00Z"),
        actionButton(ns("predict"), "Generate review-mode prediction", class = "btn-warning")
      ),
      uiOutput(ns("prediction_status")),
      uiOutput(ns("prediction_result"))
    )
  )
}

mod_prediction_server <- function(id, config, client, status) {
  moduleServer(id, function(input, output, session) {
    busy <- reactiveVal(FALSE)
    result <- reactiveVal(NULL)

    collect_record <- function() {
      fields <- setdiff(prediction_fields, "request_id")
      record <- lapply(fields, function(field) input[[field]])
      names(record) <- fields
      record$request_id <- paste0("SHINY-", toupper(substr(digest_text(Sys.time()), 1, 12)))
      record
    }

    observeEvent(input$load_example, {
      example <- synthetic_example_record()
      for (field in setdiff(names(example), "request_id")) {
        update_input_value(session, field, example[[field]])
      }
    })

    observeEvent(input$reset, {
      example <- synthetic_example_record()
      for (field in setdiff(names(example), "request_id")) {
        update_input_value(session, field, example[[field]])
      }
      result(NULL)
    })

    observeEvent(input$predict, {
      req(!busy())
      busy(TRUE)
      on.exit(busy(FALSE), add = TRUE)
      response <- tryCatch(
        api_predict(client, collect_record()),
        error = function(err) {
          api_error("validation_error", 422, safe_error_message(err))
        }
      )
      result(present_prediction(response))
    })

    output$prediction_status <- renderUI({
      if (busy()) aria_status("Prediction request in progress.") else NULL
    })

    output$prediction_result <- renderUI({
      value <- result()
      if (is.null(value)) return(NULL)
      if (!isTRUE(value$ok)) {
        return(tags$section(class = "result-error", role = "alert", value$message))
      }
      tags$section(
        class = "prediction-result",
        h2("Prediction result"),
        tags$p(class = "probability", value$probability_label),
        tags$p(strong("Risk band: "), value$risk_band),
        tags$p(strong("Predicted class: "), value$class_label),
        tags$p(strong("Selected threshold: "), value$threshold),
        tags$p(strong("Model: "), paste(value$model_family, "registry version", value$registry_version)),
        tags$p(strong("Candidate: "), value$candidate_identifier),
        tags$p(strong("Governance: "), paste(value$approval_status, value$activation_status, value$status)),
        h3("Important factors"),
        tags$p(paste(value$factors, collapse = ", ")),
        tags$p(class = "warning-text", value$explanation_warning),
        h3("Limitations"),
        tags$ul(lapply(value$limitations, tags$li)),
        tags$p(strong("Request identifier: "), value$request_id),
        tags$p("Consider whether an appropriate operational review is needed.")
      )
    })
  })
}

update_input_value <- function(session, field, value) {
  if (field %in% names(allowed_values)) {
    updateSelectInput(session, field, selected = value)
  } else if (is.numeric(value)) {
    updateNumericInput(session, field, value = value)
  } else {
    updateTextInput(session, field, value = value)
  }
}
