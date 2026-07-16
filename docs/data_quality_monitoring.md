# Data Quality Monitoring

Data quality monitoring checks whether a current synthetic monitoring window is usable before drift or performance interpretation is trusted. It validates required features, unexpected features, row counts, null rates and invalid values against the monitoring configuration.

Critical data quality findings trigger review because downstream metrics can become misleading when the input window is malformed. They do not trigger automated correction, retraining or model replacement. The correct response is to inspect source-window generation, pipeline assumptions and evidence freshness.

Milestone 11 records data quality status in `reports/monitoring/data_quality_monitoring.json`. The report is intentionally aggregate-only. It does not commit raw input rows, patient identifiers, admission identifiers, API keys, request payloads or sensitive operational values.
