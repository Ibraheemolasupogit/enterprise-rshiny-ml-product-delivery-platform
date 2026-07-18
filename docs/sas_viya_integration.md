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

## Commands

Use the default local provider:

```bash
python3 -m ml_product.cli lifecycle-describe-provider
python3 -m ml_product.cli lifecycle-check-readiness
python3 -m ml_product.cli lifecycle-build-model-package
```

Write the package to a temporary path during experiments:

```bash
python3 -m ml_product.cli lifecycle-build-model-package --output-path /tmp/model_lifecycle_package.json
```

## Offline Behaviour

`provider.selected: local` is the supported default for development and CI. Selecting `sas_viya` also requires `sas_viya.enabled: true` and a reachable Viya endpoint with local environment variables set for the configured authentication mode.

The SAS Viya client currently implements readiness and generic authenticated request handling. Later milestones can bind model registration, champion/challenger metadata and promotion operations to the concrete Viya endpoints available in the target environment.

## Planned Milestone 15.2 Work

Future work should add live SAS Viya model registration, external champion/challenger comparison, promotion evidence capture and access-control validation against an available Viya environment. Those operations remain deliberately out of scope for Milestone 15.1.
