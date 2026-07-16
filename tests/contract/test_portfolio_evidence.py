import json
from pathlib import Path


def read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_milestone_audit_is_complete_and_honest_about_external_blockers() -> None:
    payload = read_json("reports/portfolio/milestone_audit.json")
    statuses = {item["number"]: item["status"] for item in payload["milestones"]}
    assert payload["result"] == "passed"
    assert statuses[4] == "complete_with_external_blocker"
    assert statuses[8] == "complete_with_external_blocker"
    assert all(number in statuses for number in range(1, 15))
    assert payload["external_blockers"]["denodo"] == "externally blocked and not implemented"
    assert payload["external_blockers"]["sas_viya"] == "externally blocked and not implemented"


def test_evidence_integrity_preserves_governance_statuses() -> None:
    payload = read_json("reports/portfolio/evidence_integrity.json")
    assert payload["result"] == "passed"
    assert payload["identifier_consistency"] is True
    assert payload["metric_consistency"] is True
    assert payload["status_consistency"] is True
    assert payload["errors"] == []


def test_portfolio_readiness_is_not_operational_release() -> None:
    payload = read_json("reports/portfolio/portfolio_readiness.json")
    assert payload["local_review_ready"] is True
    assert payload["operational_release_ready"] is False
    assert payload["model_approval_status"] == "pending"
    assert payload["model_activation_status"] == "inactive"
    assert payload["external_deployment_status"] == "not_performed"
