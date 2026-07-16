# 0024 Human Approval Before Activation

Status: Accepted

Context: Activation changes runtime behavior and must not be inferred from metrics alone.

Decision: Activation requires an approved registry state and an explicit command with actor and reason.

Consequences: The real registry has no active model after registration because approval is not granted.

Alternatives considered: Metric-driven activation was rejected because synthetic evidence is not sufficient.
