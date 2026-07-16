governance_summary <- function(evidence) {
  manifest <- evidence$registry_manifest
  governance <- evidence$governance_review
  approval <- evidence$approval_decision
  activation <- evidence$activation_status
  list(
    identity = list(
      model_name = manifest$model_name,
      registry_version = manifest$registry_version,
      registry_identifier = manifest$registry_id,
      candidate_identifier = manifest$candidate_identifier,
      model_family = "xgboost",
      feature_build_identifier = manifest$feature_build_identifier,
      feature_count = manifest$feature_count,
      calibration = manifest$calibration,
      threshold = manifest$threshold
    ),
    state = list(
      registry_state = manifest$registry_state,
      approval_status = approval$approval_status,
      activation_status = activation$activation_state,
      governance_recommendation = governance$recommended_decision,
      serving_readiness = "review-mode only; approved operational serving unavailable"
    ),
    flags = governance$review_flags,
    hard_requirements = governance$hard_requirements,
    approval = list(
      automatic_approval = approval$automatic_approval,
      human_decision_required = governance$human_decision_required,
      current_decision = approval$decision
    )
  )
}

safe_audit_events <- function(evidence) {
  events <- evidence$registry_audit_summary$events
  lapply(events, function(event) {
    event$details <- lapply(event$details, sanitize_path_text)
    event
  })
}

model_card_summary <- function(evidence) {
  lines <- evidence$model_card
  keep <- grepl("intended|limitation|synthetic|approval|operational|clinical", lines, ignore.case = TRUE)
  head(lines[keep], 8)
}
