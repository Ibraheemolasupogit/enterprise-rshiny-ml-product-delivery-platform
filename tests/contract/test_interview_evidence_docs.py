import re
from pathlib import Path

from scripts.validate_repository import (
    CAPABILITY_STATUS_VOCABULARY,
    INTERVIEW_DIAGRAMS,
    INTERVIEW_DOCS,
    _backtick_paths,
    _markdown_links,
)


def test_interview_documentation_files_exist() -> None:
    for path in [*INTERVIEW_DOCS, *INTERVIEW_DIAGRAMS]:
        assert Path(path).is_file(), path


def test_evidence_index_has_required_schema_and_status_vocabulary() -> None:
    text = Path("docs/interview_evidence_index.md").read_text(encoding="utf-8")

    for heading in (
        "Capability",
        "Status",
        "Implementation modules",
        "CLI or Make commands",
        "Tests",
        "Evidence artifacts",
        "Documentation",
        "Limitations",
    ):
        assert heading in text
    for status in CAPABILITY_STATUS_VOCABULARY:
        assert status in text


def test_evidence_index_covers_required_capabilities_and_existing_paths() -> None:
    text = Path("docs/interview_evidence_index.md").read_text(encoding="utf-8")
    capabilities = {
        "Synthetic data",
        "Data quality",
        "PostgreSQL",
        "Denodo",
        "Feature engineering",
        "Model training",
        "Explainability",
        "Calibration",
        "Fairness",
        "Registry and governance",
        "SAS Viya package and readiness",
        "SAS Viya registration",
        "Promotion assessment",
        "Local activation",
        "Serving",
        "R Shiny",
        "Monitoring",
        "Retraining",
        "Security",
        "Release assurance",
        "Orchestration",
    }

    for capability in capabilities:
        assert f"| {capability} |" in text
    for path in _backtick_paths(text):
        assert Path(path).exists(), path


def test_readme_links_to_interview_layer_and_targets_exist() -> None:
    text = Path("README.md").read_text(encoding="utf-8")

    for path in (
        "docs/interview_architecture.md",
        "docs/interview_evidence_index.md",
        "docs/interview_demo_guide.md",
        "docs/end_to_end_lineage.md",
        "docs/portfolio_capability_map.md",
    ):
        assert path in text
    for link in _markdown_links(text):
        if link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = link.split("#", 1)[0]
        if target:
            assert Path(target).exists(), link


def test_interview_docs_disclose_boundaries_and_synthetic_data() -> None:
    combined = "\n".join(Path(path).read_text(encoding="utf-8").lower() for path in INTERVIEW_DOCS)

    assert "synthetic" in combined
    assert "external promotion never activates the local model" in combined
    assert "local activation remains a separate" in combined
    assert "requires_external_environment" in combined
    assert "live sas viya registration and promotion" in combined


def test_interview_docs_do_not_claim_unsupported_live_sas_or_clinical_deployment() -> None:
    combined = "\n".join(
        [
            Path("README.md").read_text(encoding="utf-8"),
            *(Path(path).read_text(encoding="utf-8") for path in INTERVIEW_DOCS),
        ]
    ).lower()

    prohibited = [
        "live sas viya validated",
        "live sas viya registration validated",
        "live sas viya promotion validated",
        "real clinical deployment",
        "real patient outcome",
    ]
    for phrase in prohibited:
        assert phrase not in combined


def test_architecture_diagram_is_mermaid_source_with_required_boundaries() -> None:
    text = Path("docs/diagrams/interview-architecture.mmd").read_text(encoding="utf-8")

    assert text.startswith("flowchart")
    for phrase in (
        "DataPlane",
        "ControlPlane",
        "EvidencePlane",
        "external state only",
        "separate governed local action",
    ):
        assert phrase in text
    assert re.search(r"Source\s*-->", text)
