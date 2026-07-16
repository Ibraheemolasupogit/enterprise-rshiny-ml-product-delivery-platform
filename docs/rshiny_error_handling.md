# R-Shiny Error Handling

Milestone 10 defines stable user-facing error categories: configuration error, API unavailable, API not ready, authentication error, authorisation error, validation error, batch limit error, malformed response, evidence unavailable, evidence mismatch, feedback write error, and unexpected error.

Messages are sanitised before display. They do not expose API keys, raw payloads, stack traces, model artefact paths, local user paths, or processed data paths. Request identifiers may be shown when the API provides them.

The UI remains usable after failed prediction, upload validation, evidence loading, or feedback operations.
