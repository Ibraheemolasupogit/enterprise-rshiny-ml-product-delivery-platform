# ADR 0036: Uploaded Synthetic Data Is Not Retained

Status: Accepted

Context: Cohort uploads are synthetic but still should not create unnecessary local artefacts.

Decision: Uploaded CSV files are read from Shiny's temporary upload path and not copied into repository or server storage.

Consequences: Users can re-upload templates when needed; the product avoids accidental data retention.

Alternatives considered: Persisted upload history was rejected because it belongs to later monitoring or audit work.
