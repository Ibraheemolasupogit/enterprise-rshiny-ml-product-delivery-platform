# Monitoring Alerts

Monitoring alerts are deterministic summaries of warning and critical findings across schema, data quality, drift, prediction, performance, calibration and operational sections. Each alert has a stable identifier, severity, section, reason and automatic action.

The only automatic action allowed in Milestone 11 is `human_review_required`. The overall review record keeps `automatic_action` as `none`, because alert generation is not a workflow engine. It does not retrain, promote, approve, activate, deploy, replace or roll back models.

Alert evidence is committed in `reports/monitoring/monitoring_alerts.json` and displayed by the R-Shiny Monitoring page. Users should treat alerts as triage signals and consult the underlying section evidence before making any governance recommendation.
