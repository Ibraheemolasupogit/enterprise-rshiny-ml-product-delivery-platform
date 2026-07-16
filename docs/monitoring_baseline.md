# Monitoring Baseline

The monitoring baseline is built from the locked training feature matrix and target split already produced for the model development milestone. It records feature distributions, missingness, synthetic prediction distributions, calibration reference points, selected threshold metadata and feature fingerprints.

The baseline exists to support reproducible comparison, not to certify clinical performance. It is generated from deterministic synthetic data and carries the same candidate identifier as the registered model evidence. Rebuilding the baseline should produce the same identifier when the upstream evidence is unchanged.

The committed baseline manifest in `reports/monitoring/monitoring_baseline_manifest.json` is the stable audit record. The fuller generated baseline under `monitoring/reports` is local evidence and must not contain secrets, absolute workstation paths, identifiers, raw request payloads or real patient data.
