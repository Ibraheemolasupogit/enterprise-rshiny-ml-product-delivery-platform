# R-Shiny Developer Guide

The Shiny app lives under `rshiny/`.

- `app.R`, `global.R`, `config.R`: application entry and shared sourcing.
- `R/`: API client, configuration, validation, presentation and utility functions.
- `modules/`: overview, prediction, feedback and status banner modules.
- `tests/testthat/`: deterministic R unit tests.
- `tests/shinytest2/`: bounded UI test configuration.

Dependencies are managed with `renv` and recorded in `renv.lock`. Restore with:

```bash
Rscript -e 'renv::restore(prompt = FALSE)'
```

Environment variables:

- `MODEL_API_BASE_URL`
- `MODEL_API_KEY`
- `SHINY_APP_ENV`
- `SHINY_REQUEST_TIMEOUT_SECONDS`

Run R validation:

```bash
make test-rshiny
```
## Milestone 10 Developer Notes

Batch validation lives in `rshiny/R/batch_validation.R`, API parsing in `rshiny/R/batch_presenter.R`, export shaping in `rshiny/R/export_utils.R`, and evidence loading in `rshiny/R/evidence_client.R`.

Run `make test-rshiny-advanced` for R lint, unit tests, browser-backed Shiny tests, UAT evidence validation, and single/batch FastAPI smoke tests. Browser tests require Chrome or Chromium through `shinytest2`.
