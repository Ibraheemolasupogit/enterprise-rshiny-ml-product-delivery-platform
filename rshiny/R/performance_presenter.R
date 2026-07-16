performance_summary <- function(evidence) {
  comparison <- evidence$model_comparison$rows
  validation_xgb <- comparison[[which(vapply(
    comparison,
    function(row) identical(row$model_family, "xgboost"),
    logical(1)
  ))]]
  test <- evidence$test_metrics$metrics
  list(
    recommended_model = evidence$candidate_recommendation$recommended_model,
    selected_threshold = evidence$candidate_recommendation$selected_threshold,
    calibration = evidence$candidate_recommendation$recommended_calibration,
    approval_status = evidence$approval_decision$approval_status,
    activation_status = evidence$activation_status$activation_state,
    validation = validation_xgb,
    test = test,
    degradation = list(
      pr_auc = validation_xgb$pr_auc - test$pr_auc,
      roc_auc = validation_xgb$roc_auc - test$roc_auc,
      balanced_accuracy = validation_xgb$balanced_accuracy - test$balanced_accuracy,
      specificity = validation_xgb$specificity - test$specificity
    )
  )
}

metrics_table <- function(rows) {
  data.frame(
    model = vapply(rows, function(row) row$model_family, character(1)),
    roc_auc = vapply(rows, function(row) row$roc_auc, numeric(1)),
    pr_auc = vapply(rows, function(row) row$pr_auc, numeric(1)),
    pr_auc_lift = vapply(rows, function(row) row$pr_auc_lift_over_prevalence, numeric(1)),
    brier = vapply(rows, function(row) row$brier_score, numeric(1)),
    log_loss = vapply(rows, function(row) row$log_loss, numeric(1)),
    precision = vapply(rows, function(row) row$precision, numeric(1)),
    recall = vapply(rows, function(row) row$recall, numeric(1)),
    specificity = vapply(rows, function(row) row$specificity, numeric(1)),
    f1 = vapply(rows, function(row) row$f1, numeric(1)),
    balanced_accuracy = vapply(rows, function(row) row$balanced_accuracy, numeric(1)),
    stringsAsFactors = FALSE
  )
}
