# R-Shiny Exports

Cohort exports are CSV files named `synthetic_cohort_predictions_<timestamp>.csv`. They include row number, long-stay probability, predicted class, risk band, registry version, model family, threshold, review-mode status, candidate identifier, synthetic-data statement, and export timestamp.

Exports exclude API keys, local filesystem paths, stack traces, hidden transformed features, unnecessary raw inputs, identifiers, and outcome fields. The app does not persist exports server-side after the response completes.
