# ADR 0059: Model Binaries Are Generated Or Mounted, Not Committed

Status: Accepted

Context: Model and preprocessor binaries are generated artefacts and may be large or environment-specific. Committing them would obscure reproducibility and pollute release inventory.

Decision: Keep binaries ignored. Local and CI container validation may generate or mount required artefacts, while committed registry metadata records expected artefact contracts.

Consequences: Builds require deterministic artefact preparation, and readiness fails when artefacts are absent rather than silently falling back.

Alternatives considered: Committing model binaries was rejected because it conflicts with governance and repository hygiene.
