# Threshold Selection

Milestone 6 selects thresholds using validation probabilities only. Candidate thresholds run from 0.10 to 0.90 in 0.05 increments. The deterministic rule retains thresholds meeting the minimum recall requirement, selects highest precision, breaks ties by lowest weighted cost, and then by lowest threshold.

The selected threshold is locked before test evaluation. Test metrics do not alter the candidate, calibration method, or threshold.
