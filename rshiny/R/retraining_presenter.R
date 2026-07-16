retraining_status_table <- function(evidence) {
  data.frame(
    field = c("Monitoring run", "Eligibility", "Recommendation", "Champion retained",
              "Registration eligible", "Automatic action", "Approval", "Activation",
              "Deployment"),
    value = c(
      evidence$eligibility$monitoring_run_identifier,
      evidence$eligibility$eligibility_result,
      evidence$recommendation$recommendation,
      as.character(evidence$recommendation$champion_retained),
      as.character(evidence$recommendation$registration_eligible),
      evidence$recommendation$automatic_action,
      evidence$recommendation$approval_status,
      evidence$recommendation$activation_status,
      evidence$recommendation$deployment_status
    ),
    stringsAsFactors = FALSE
  )
}

retraining_challenger_table <- function(evidence) {
  rows <- evidence$challengers$rows
  data.frame(
    model_family = vapply(rows, function(row) row$model_family, character(1)),
    candidate_identifier = vapply(rows, function(row) row$candidate_identifier, character(1)),
    pr_auc = vapply(rows, function(row) row$pr_auc, numeric(1)),
    roc_auc = vapply(rows, function(row) row$roc_auc, numeric(1)),
    brier_score = vapply(rows, function(row) row$brier_score, numeric(1)),
    recall = vapply(rows, function(row) row$recall, numeric(1)),
    specificity = vapply(rows, function(row) row$specificity, numeric(1)),
    threshold = vapply(rows, function(row) row$threshold, numeric(1)),
    reproducible = vapply(rows, function(row) as.character(row$reproducible), character(1)),
    stringsAsFactors = FALSE
  )
}

retraining_gate_table <- function(evidence) {
  hard <- evidence$gates$hard_gates
  data.frame(
    gate = names(hard),
    passed = vapply(hard, as.character, character(1)),
    stringsAsFactors = FALSE
  )
}
