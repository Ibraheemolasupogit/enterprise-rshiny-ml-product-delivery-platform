# ADR 0060: Operational Release Requires Approved Active Model

Status: Accepted

Context: The current model is registered but pending approval and inactive. CI success alone must not convert a candidate into an operational model.

Decision: Operational release gates require both approval and activation evidence. The current release readiness is therefore blocked for operational release.

Consequences: Local review can proceed with labels, but production-like serving remains unavailable until governance decisions are made manually.

Alternatives considered: Allowing operational release with a pending model was rejected as a governance bypass.
