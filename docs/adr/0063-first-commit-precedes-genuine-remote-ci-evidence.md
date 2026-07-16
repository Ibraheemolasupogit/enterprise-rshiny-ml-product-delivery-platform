# ADR 0063: First Commit Precedes Genuine Remote CI Evidence

Status: Accepted

Context: The repository currently has no commits. GitHub-hosted Actions cannot have valid run IDs or URLs before a push.

Decision: Release evidence must state that remote CI has not executed and that local validation is local-equivalent only.

Consequences: The project avoids fabricated CI claims. The first commit and push become a documented manual activation step.

Alternatives considered: Creating placeholder run links was rejected because it would misrepresent assurance.
