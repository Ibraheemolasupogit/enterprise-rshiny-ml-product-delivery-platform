# Dataset Splitting

Milestone 5 uses deterministic temporal patient-group splitting. Patients are ordered by their first admission datetime and then by `patient_id`. Whole patient groups are allocated to train, validation, and test to approximate 60/20/20 row-count fractions.

The patient-group rule takes priority over perfect chronological row boundaries. Because the synthetic data can include multiple admissions for the same patient, a training patient can have later admissions than some validation or test patients. This is documented as a small-sample trade-off and prevents the higher-risk contamination where the same patient appears in multiple splits.

The committed split summary records row counts, patient counts, positive counts, positive rates, minimum and maximum admission dates, patient overlap count, admission overlap count, allocation strategy, seed, and split fingerprint. The current build reports zero patient overlap and zero admission overlap.

Changing the split fractions changes the split fingerprint deterministically. The reproducibility script builds the same source twice and confirms identical feature content, split assignments, feature ordering, and preprocessing metadata, then changes the split configuration to confirm a different fingerprint.
