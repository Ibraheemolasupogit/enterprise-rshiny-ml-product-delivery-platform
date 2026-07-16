# ADR 0038: Model Governance View Is Read Only

Status: Accepted

Context: Approval, activation, rollback, and deployment require governed processes outside this Shiny product milestone.

Decision: The governance page displays registry and review evidence but exposes no mutation controls.

Consequences: The candidate remains registered, pending, inactive, and deferred.

Alternatives considered: Admin buttons were rejected because they would bypass governance.
