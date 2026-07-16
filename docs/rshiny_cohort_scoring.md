# R-Shiny Cohort Scoring

Milestone 10 adds synthetic cohort scoring through the FastAPI `/v1/predict/batch` endpoint. The Shiny app validates a CSV upload, sends valid synthetic rows to FastAPI, presents bounded results, and offers a local CSV download.

The CSV contract uses the same raw admission-time predictors as single prediction. It accepts CSV only, requires the template column order, rejects unknown columns, rejects duplicate columns, rejects identifiers and outcome fields, and enforces a maximum of 100 rows and 2 MB.

Uploads are not retained. Results are review-mode only and labelled as generated from synthetic inputs using an unapproved model in local review mode.
