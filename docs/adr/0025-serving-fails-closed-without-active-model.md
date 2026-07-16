# 0025 Serving Fails Closed Without Active Model

Status: Accepted

Context: The API must not silently serve an unapproved candidate.

Decision: Liveness can pass without a model, but readiness and prediction require an approved active model unless explicit local review mode is enabled.

Consequences: Default serving is safe but not ready in the committed registry state.

Alternatives considered: Loading the latest registered model by default was rejected.
