# Model Serving

Milestone 7 adds a local FastAPI scoring API. Startup validates the registry, resolves an approved active model by default, loads the matching preprocessor and model artefacts, and validates feature compatibility. If no approved active model exists, liveness passes but readiness and prediction fail closed.

The service accepts raw admission-time predictors, applies the registered preprocessing contract, generates calibrated probability, applies the registered threshold, returns a separate risk band, and includes concise non-causal explanation metadata.

The service does not train models, rebuild features, query the database, deploy externally, or provide R-Shiny behaviour. Review mode is disabled by default and is explicitly not operational use.
