from pathlib import Path


def test_final_documentation_files_exist() -> None:
    required = [
        "docs/portfolio_case_study.md",
        "docs/interview_model_answer.md",
        "docs/interview_questions_and_answers.md",
        "docs/architecture_overview.md",
        "docs/end_to_end_data_flow.md",
        "docs/end_to_end_model_flow.md",
        "docs/end_to_end_serving_flow.md",
        "docs/end_to_end_governance_flow.md",
        "docs/end_to_end_delivery_flow.md",
        "docs/portfolio_screenshot_runbook.md",
        "docs/milestones/milestone-14.md",
    ]
    for path in required:
        assert Path(path).is_file(), path


def test_readme_contains_final_portfolio_sections_and_no_operational_release_claim() -> None:
    text = Path("README.md").read_text(encoding="utf-8").lower()
    required = [
        "executive summary",
        "product outcome",
        "architecture",
        "technology stack",
        "local review-mode runbook",
        "model results",
        "governance status",
        "r-shiny screenshots placeholder",
        "ci/cd",
        "security assurance",
        "commercial-tool boundaries",
        "interview relevance",
        "licence",
    ]
    for phrase in required:
        assert phrase in text
    assert "operational release readiness: blocked" in text
    assert "model approval granted: no" in text
    assert "model activation performed: no" in text


def test_portfolio_narrative_references_core_evidence_boundaries() -> None:
    text = Path("docs/portfolio_case_study.md").read_text(encoding="utf-8").lower()
    for phrase in [
        "synthetic healthcare data",
        "duckdb",
        "fastapi",
        "r-shiny",
        "retain_champion",
        "denodo",
        "sas viya",
        "operational release remains blocked",
    ]:
        assert phrase in text
