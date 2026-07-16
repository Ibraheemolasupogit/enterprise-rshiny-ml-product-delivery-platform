import json
from pathlib import Path


def test_security_summary_contract() -> None:
    payload = json.loads(
        Path("reports/assurance/security_scan_summary.json").read_text(encoding="utf-8")
    )
    assert payload["secrets"]["status"] == "passed"
    assert payload["overall_status"] == "passed"
    assert payload["python_dependency_audit"]["tool"] == "pip-audit"
    assert payload["container_vulnerability_scan"]["tool"] == "trivy"
