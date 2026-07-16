# ADR 0037: Performance Dashboard Uses Locked Evidence

Status: Accepted

Context: Shiny feedback and synthetic uploads are not evaluation data.

Decision: The performance page reads committed model-evaluation evidence only and does not recalculate live metrics.

Consequences: Validation/test separation stays intact and the dashboard cannot imply production monitoring.

Alternatives considered: Live metric aggregation was rejected as Milestone 11 scope.
