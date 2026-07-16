# Model Registry

Milestone 7 implements a local filesystem-backed registry as the reproducible baseline for model lifecycle governance. Metadata is stored in `models/registry.json`; binary artefacts are stored under ignored version directories such as `models/registered/v000001`.

Registry states are `candidate`, `registered`, `approval_pending`, `approved`, `active`, `rejected`, `retired`, and `archived`. Registration records immutable metadata and artefact checksums. It does not grant approval, activate a model, deploy a model, or register with an external platform.

The registry preserves the Milestone 6 evidence for `CAND-85EA9202CAD6FE7F`, including validation and locked test metrics. Future SAS Viya mapping may use this metadata, but no SAS Viya integration is implemented here.
