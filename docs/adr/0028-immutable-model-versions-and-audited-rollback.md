# 0028 Immutable Model Versions And Audited Rollback

Status: Accepted

Context: Registry versions and rollback history must be traceable.

Decision: Registered versions are immutable, rollback validates target status, and audit events are retained.

Consequences: Duplicate candidate registration is rejected and rollback is demonstrated with fixtures.

Alternatives considered: Mutable version records were rejected because they obscure governance history.
