# Monitoring Architecture

Milestone 11 introduces a deterministic local monitoring layer for the registered synthetic model candidate. The layer reads locked feature, registry, serving and evaluation evidence, builds a monitoring baseline from the training split, and compares synthetic current-window fixtures against that baseline.

The architecture is file based. Python owns baseline construction, window validation, drift metrics, performance metrics, alert generation and evidence writing. R-Shiny owns read-only presentation of the committed evidence in `reports/monitoring`. The monitoring workflow never opens model artefacts for mutation, never retrains, never changes thresholds, and never writes approval, activation or rollback state.

Monitoring covers schema checks, data quality, numeric drift, categorical drift, missingness, prediction distribution drift, labelled model performance, calibration stability and operational log summaries. Alerts are advisory. Their only automatic action is human review, which keeps model governance separate from monitoring detection.
