# ADR 0030 - Review Mode Status Is Always Visible

Status: Accepted

Context: The registered model is not approved or active.

Decision: A persistent banner displays review-mode or unavailable status on every Shiny page.

Consequences: Users cannot miss the unapproved synthetic status. The app avoids green production-ready styling.

Alternatives considered: page-specific notices only. Rejected because status could be missed during navigation.
