# Operational Monitoring

Operational monitoring summarises synthetic prediction event logs for latency, success counts, error rates, review-mode flags and model-version consistency. The serving logger records operational metadata and model outputs, but it deliberately excludes raw input payloads, identifiers and secrets.

Milestone 11 uses small synthetic event fixtures to prove the monitoring contract. These fixtures are not production telemetry and do not contain real patients. Generated event logs under `data/monitoring` should remain local or ignored unless a future milestone explicitly defines a committed fixture contract.

Operational alerts request service review when latency or error thresholds are exceeded. They do not activate a model, roll back a version, change serving configuration or mutate the registry.
