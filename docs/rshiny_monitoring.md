# R-Shiny Monitoring

The R-Shiny Monitoring page presents Milestone 11 evidence from `reports/monitoring` in a read-only workflow. It shows current status, data quality, feature drift, prediction drift, labelled performance, operational metrics, alerts and next-step guidance.

The page does not call Python modelling code, load model artefacts, connect to DuckDB, use reticulate, or read raw monitoring inputs. It consumes committed aggregate evidence through the same fail-closed pattern used by the performance and governance pages.

The UI must not include buttons or controls for retraining, promotion, approval, activation, deployment, rollback or threshold changes. It must clearly state that prediction drift is not performance drift without labels and that alerts trigger human review only.
