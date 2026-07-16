# Calibration Monitoring

Calibration monitoring checks whether current labelled probabilities remain aligned with observed synthetic outcomes. It records aggregate calibration error and Brier movement against the baseline reference. The existing calibration method and threshold remain locked.

The monitoring job can identify that calibration evidence needs review, but it cannot recalibrate the model. This distinction matters because automatic recalibration would mutate the prediction contract and could change user-facing risk interpretation without governance approval.

Milestone 11 calibration evidence is stored in `reports/monitoring/calibration_monitoring.json`. It is read by the R-Shiny monitoring page as status evidence only and is not connected to any update, approval or deployment control.
