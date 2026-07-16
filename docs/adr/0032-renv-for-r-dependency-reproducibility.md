# ADR 0032 - renv For R Dependency Reproducibility

Status: Accepted

Context: The R-Shiny MVP needs reproducible package installation.

Decision: Use `renv` and a generated `renv.lock`.

Consequences: Local and CI runs restore the same package set. The local `renv/library` remains ignored.

Alternatives considered: ad hoc `install.packages()` in tests. Rejected because it is less reproducible.
