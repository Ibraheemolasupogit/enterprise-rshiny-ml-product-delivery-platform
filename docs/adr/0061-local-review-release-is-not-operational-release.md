# ADR 0061: Local Review Release Is Not Operational Release

Status: Accepted

Context: Review mode is useful for technical validation but can be misread as production readiness if not labelled.

Decision: Local review release is a separate state. It is explicitly labelled local, unapproved, and not for operational use.

Consequences: Smoke tests can exercise predictions in review mode while default governed mode remains not ready and rejects predictions.

Alternatives considered: Disabling review mode entirely was rejected because it would prevent bounded integration validation.
