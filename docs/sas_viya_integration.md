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

## Champion-Challenger Lifecycle

Milestone 15.3 adds provider-neutral champion-challenger and external promotion controls. A challenger is the registered local model package plus any external SAS Viya linkage. The champion is the current lifecycle provider champion, which may be absent locally because this repository intentionally ships with no approved active model.

Promotion eligibility is built from existing evidence:

- candidate recommendation and registry status
- evaluation metrics
- threshold and calibration evidence
- fairness summary
- governance hard requirements
- approval decision
- external registration linkage
- reconciliation status

Blocked-promotion examples include missing external registration, missing or rejected governance approval, material metadata mismatch, absent evaluation evidence, failed governance hard requirements, or a package that does not match the registered external version.

## Promotion Sequence

Dry-run assessment:

```bash
python3 -m ml_product.cli lifecycle-show-champion
python3 -m ml_product.cli lifecycle-list-challengers
python3 -m ml_product.cli lifecycle-compare-champion
python3 -m ml_product.cli lifecycle-assess-promotion --dry-run
python3 -m ml_product.cli lifecycle-show-promotion
python3 -m ml_product.cli lifecycle-reconcile-promotion
```

Live external promotion requires a SAS Viya config, prior external registration, matching reconciliation state, governance approval and an explicit confirmation flag:

```bash
python3 -m ml_product.cli lifecycle-submit-promotion --confirm-external-promotion
```

Repeated promotion of the current external champion returns `already_champion` and does not issue duplicate promotion requests.

## Promotion Versus Activation

SAS Viya promotion updates only external lifecycle/champion state. Local model activation remains a separate explicit governed registry command. External promotion never modifies `models/registry.json`, never activates the FastAPI serving model, and never changes rollback state. Promotion evidence reports whether external champion state and local activation state are aligned or divergent.

Rollback boundaries remain unchanged: local rollback uses the existing registry rollback workflow, while any future SAS Viya rollback or champion reassignment must be explicit and separately evidenced.

## Commands

Use the default local provider:

```bash
python3 -m ml_product.cli lifecycle-describe-provider
python3 -m ml_product.cli lifecycle-check-readiness
python3 -m ml_product.cli lifecycle-build-model-package
python3 -m ml_product.cli lifecycle-register-model --dry-run
python3 -m ml_product.cli lifecycle-show-registration
python3 -m ml_product.cli lifecycle-reconcile-registration
python3 -m ml_product.cli lifecycle-show-champion
python3 -m ml_product.cli lifecycle-list-challengers
python3 -m ml_product.cli lifecycle-compare-champion
python3 -m ml_product.cli lifecycle-assess-promotion --dry-run
python3 -m ml_product.cli lifecycle-show-promotion
python3 -m ml_product.cli lifecycle-reconcile-promotion
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

Milestone 15.3 adds champion-challenger comparison, approval-aware promotion assessment and external-only promotion controls. Future work should add production access-control validation, richer SAS Viya workflow state mapping, human workflow callbacks and release-operation integration against an available Viya environment.
