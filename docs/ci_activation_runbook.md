# CI Activation Runbook

CI is not genuinely executed until the first commit is pushed to the configured remote. After push, inspect every workflow result in GitHub Actions, compare remote failures with local validation evidence, and update `reports/assurance/ci_local_validation.json` only after a new local evidence build.

Do not treat local workflow validation as a substitute for remote CI. Local validation proves the workflow contract and equivalent commands are coherent; it does not create remote run IDs, URLs, badges, or hosted-runner evidence.
