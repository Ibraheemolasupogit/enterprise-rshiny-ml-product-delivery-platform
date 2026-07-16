# Model Rollback

Rollback is implemented as a governed registry operation. Rollback targets must be approved-compatible versions, artefacts are revalidated, dry-run mode does not mutate state, and audit events are retained.

The real committed registry contains only one registered unapproved candidate. Rollback behavior is demonstrated in tests with clearly labelled fixtures rather than fabricated production model history.
