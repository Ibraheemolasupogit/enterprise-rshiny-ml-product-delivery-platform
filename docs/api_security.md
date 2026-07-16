# API Security

The local API uses an API key from the `MODEL_API_KEY` environment variable. No API key is committed. Liveness is public; metadata and prediction endpoints require authentication.

Prediction logging writes structured event metadata only. It does not log API keys, full raw inputs, patient identifiers, admission identifiers, or outcome values.

Input validation rejects unexpected fields, invalid categories, invalid numeric ranges, outcome fields, and identifiers. OAuth/OIDC, rate limiting, and enterprise identity are future production requirements.

The R-Shiny MVP reads `MODEL_API_BASE_URL` and `MODEL_API_KEY` from environment variables only. Local Shiny development CORS is restricted to `http://127.0.0.1:3838` and `http://localhost:3838`; wildcard origins and credentialed CORS are not enabled.
