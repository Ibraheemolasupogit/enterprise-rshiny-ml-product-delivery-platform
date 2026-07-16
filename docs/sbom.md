# SBOM

Milestone 13 defines SBOM generation for the repository filesystem, the FastAPI image, and the R-Shiny image. CI uses Syft-compatible generation through a GitHub Action and stores SBOMs as CI artefacts rather than publishing them externally.

The committed `reports/assurance/sbom_manifest.json` is a small manifest that records artefact names, formats, component counts where locally known, generator policy, image digest status, and the fact that images are local and unpublished.
