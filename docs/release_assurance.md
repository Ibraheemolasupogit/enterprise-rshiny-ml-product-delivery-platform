# Release Assurance

Release assurance evaluates whether the current repository state can support a local review release and whether it is eligible for operational release. The current state is ready for local review only and blocked for operational release because there is no approved active model.

Committed evidence lives under `reports/assurance`. It records workflow inventory, dependency assurance, security summaries, SBOM manifests, container validation, local deployment smoke expectations, and explicit remote CI status. Remote CI is reported as not executed because the repository has no commits and has not been pushed.
