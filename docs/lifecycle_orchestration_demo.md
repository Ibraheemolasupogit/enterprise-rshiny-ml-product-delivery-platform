# Lifecycle Orchestration Demo

Milestone 15.4 provides a canonical end-to-end lifecycle workflow for local review and interview demonstration. It coordinates existing repository capabilities across data readiness, governed logical views, feature evidence, model evaluation, lifecycle registration, promotion assessment, approval gates, serving validation, monitoring baseline evidence and release readiness.

The orchestration layer does not approve, activate, deploy, roll back or retrain a model. It records what is ready, blocked, skipped or failed, then writes consolidated credential-free evidence.

## Modes

- `local_safe`: default offline run using the local provider and existing filesystem registry.
- `enterprise_dry_run`: enterprise-shaped workflow without live PostgreSQL, Denodo or SAS Viya mutations.
- `enterprise_live`: reserved for explicitly confirmed live provider actions.

Offline and dry-run modes force mutation flags to `false` for external registration, external promotion and local activation. Local activation remains a separate governed registry command in every mode.

## Commands

Build the review artifacts first when starting from a clean checkout:

```bash
make build-review-artifacts
```

Run the local workflow:

```bash
make lifecycle-e2e-local
```

Run the enterprise dry run:

```bash
make lifecycle-e2e-dry-run
```

Inspect and validate evidence:

```bash
make lifecycle-e2e-show
make lifecycle-e2e-validate
```

Equivalent CLI commands:

```bash
python3 -m ml_product.cli lifecycle-run-end-to-end --mode local_safe
python3 -m ml_product.cli lifecycle-run-end-to-end --mode enterprise_dry_run --dry-run
python3 -m ml_product.cli lifecycle-show-workflow
python3 -m ml_product.cli lifecycle-resume-workflow
python3 -m ml_product.cli lifecycle-validate-workflow-evidence
```

## Evidence

The latest state is written to `reports/model_evaluation/lifecycle_workflow_state.json`. Consolidated evidence bundles are written to `reports/model_evaluation/lifecycle_workflows/`.

Each bundle includes:

- workflow id, mode and fingerprints
- ordered stage results
- gate decisions and blocking reasons
- mutation flags
- promotion and activation boundary evidence
- resume metadata
- known offline limitations
- checksum

Credential values and authentication material are not written to workflow evidence.

## Resume

Resume is guarded by the lifecycle configuration fingerprint and the model package fingerprint:

```bash
python3 -m ml_product.cli lifecycle-resume-workflow
```

Use `--restart-stage` to explicitly rerun from a known stage after correcting a local problem:

```bash
python3 -m ml_product.cli lifecycle-resume-workflow --restart-stage promotion_assessment
```

If the configuration or package identity changed, start a fresh workflow rather than resuming stale evidence.

## Interview Boundary

For demonstrations, use `local_safe` or `enterprise_dry_run`. These modes show the whole product lifecycle while honestly preserving the current governance state: the candidate is review-only, pending approval, inactive for operations and not deployed.
