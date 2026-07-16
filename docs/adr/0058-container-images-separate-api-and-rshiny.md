# ADR 0058: Container Images Separate API and R-Shiny

Status: Accepted

Context: The product has a Python FastAPI scoring boundary and an R-Shiny user interface boundary. Mixing these runtimes would increase attack surface and blur ownership.

Decision: Build separate API and R-Shiny images. The R-Shiny image does not contain the Python scoring runtime or model files.

Consequences: Runtime responsibilities remain clear, local Compose can validate dependency readiness, and future operational hardening can happen per service.

Alternatives considered: A combined image was rejected because it would weaken service isolation.
