# SAS Viya Model-Lifecycle Integration

Milestone 15.1 adds a provider-neutral model-lifecycle boundary. SAS Viya is an optional enterprise model-management provider; it does not replace the Python feature engineering, model training, evaluation, registry evidence, serving API, R Shiny review application, monitoring or retraining workflows.

The default local provider remains `local_model_lifecycle` and delegates to the existing filesystem registry and governance workflow. CI and local tests do not require a live SAS Viya environment.

## Architecture Role

Current flow:

```text
PostgreSQL -> Denodo -> feature engineering -> Python model training/evaluation
  -> lifecycle provider
       -> local registry
       -> SAS Viya boundary
  -> approval/promotion -> API and R Shiny -> monitoring and retraining
```

Registration package generation is review-only. It builds JSON evidence for a lifecycle provider without approving, activating, deploying or changing the current champion.

## Configuration

Lifecycle configuration lives in `config/model_lifecycle.yaml`.

Non-secret SAS Viya settings include:

- provider selection
- base URL
- authentication mode
- project and repository identifiers
- model name
- readiness path
- timeout
- TLS verification
- enabled flag

Secret values are never committed. The config declares only the environment-variable names used by a live SAS Viya client:

- `SAS_VIYA_CLIENT_ID`
- `SAS_VIYA_CLIENT_SECRET`
- `SAS_VIYA_ACCESS_TOKEN`

`.env.example` documents these names in comments only.

Endpoint paths are isolated in `sas_viya.endpoints` because Viya deployments can expose different routing conventions. The configured templates cover repository lookup, model lookup, model creation, model-version lookup, model-version creation, metadata update, model retrieval and model-version retrieval.

## Registration Sequence

`lifecycle-register-model` follows this sequence for the selected provider:

1. Build and validate the provider-neutral model lifecycle package.
2. Compute a deterministic registration fingerprint.
3. Resolve the target SAS Viya repository or project.
4. Search for an existing model by deterministic model identity.
5. Create the model only if absent.
6. Search for an existing model version by registration fingerprint.
7. Create the model version only if absent.
8. Synchronise supported metadata.
9. Retrieve/reconcile external metadata.
10. Write credential-free registration evidence and local linkage.

Registration does not mean approval, promotion, activation or deployment.

## Idempotency

The registration fingerprint is derived from stable package fields:

- model name
- local model version and candidate identifier
- training dataset version
- source fingerprint
- model family
- prediction point
- artefact checksums

Current timestamps are not part of the fingerprint. Re-running registration for the same package should return `already_registered` after finding the existing model and version.

## Metadata Mapping

The SAS Viya metadata mapping stores supported fields as model/version properties and custom metadata. Mapped fields include model family, target column, prediction point, dataset version, source fingerprint, feature count, selected threshold and calibration, registry status, synthetic-data declaration, local registry id, candidate identifier and registration fingerprint.

Richer local evidence such as metrics, fairness, threshold/calibration detail and governance state is kept in structured custom payloads where a Viya deployment does not expose native fields.

## Linkage Store

The local linkage store records the relationship between the local registry version and the external SAS Viya ids:

- provider
- local model id and version
- local build identifier
- registration fingerprint
- external repository, model and model-version ids
- metadata sync status
- registration/reconciliation timestamps
- evidence path and checksum

The store is deterministic JSON, written atomically, and contains no credentials. It does not mutate `models/registry.json`.

## Reconciliation

Reconciliation compares local package metadata, external custom properties and any linkage record. Exact matches are reported separately from missing external fields and material mismatches. Material mismatches are surfaced rather than silently overwritten. Milestone 15.2 only performs safe metadata synchronisation of the configured custom metadata fields.

## Commands

Use the default local provider:

```bash
python3 -m ml_product.cli lifecycle-describe-provider
python3 -m ml_product.cli lifecycle-check-readiness
python3 -m ml_product.cli lifecycle-build-model-package
python3 -m ml_product.cli lifecycle-register-model --dry-run
python3 -m ml_product.cli lifecycle-show-registration
python3 -m ml_product.cli lifecycle-reconcile-registration
```

Write the package to a temporary path during experiments:

```bash
python3 -m ml_product.cli lifecycle-build-model-package --output-path /tmp/model_lifecycle_package.json
```

## Offline Behaviour

`provider.selected: local` is the supported default for development and CI. Selecting `sas_viya` also requires `sas_viya.enabled: true` and a reachable Viya endpoint with local environment variables set for the configured authentication mode.

The SAS Viya client currently implements readiness and generic authenticated request handling. Later milestones can bind model registration, champion/challenger metadata and promotion operations to the concrete Viya endpoints available in the target environment.

For live SAS Viya registration, create a separate local config that sets `provider.selected: sas_viya`, `sas_viya.enabled: true`, the target endpoint templates and local environment variables for the chosen authentication mode. CI should continue to use the default local provider and mocked transport tests.

## Future Work

Milestone 15.2 adds deterministic registration and metadata synchronisation. Future work should add external champion/challenger comparison, promotion evidence capture, approval workflow integration and access-control validation against an available Viya environment.
