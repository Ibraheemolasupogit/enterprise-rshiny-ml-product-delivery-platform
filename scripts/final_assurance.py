"""Run final offline assurance and write a deterministic summary report."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "reports" / "assurance" / "final_assurance.json"
DISPOSABLE_ARTIFACTS = (
    ROOT / ".coverage",
    ROOT / "data" / "monitoring" / "prediction_events.jsonl",
)


@dataclass(frozen=True)
class AssuranceStep:
    name: str
    command: tuple[str, ...]
    category: str
    required: bool = True


MANDATORY_STEPS = [
    AssuranceStep(
        "clean_checkout_review_artifact_reconstruction",
        ("make", "build-review-artifacts"),
        "reconstruction",
    ),
    AssuranceStep("python_lint", ("python3", "-m", "ruff", "check", "."), "quality"),
    AssuranceStep("python_typecheck", ("python3", "-m", "mypy", "src"), "quality"),
    AssuranceStep(
        "contract_tests",
        ("python3", "-m", "pytest", "-q", "tests/contract"),
        "tests",
    ),
    AssuranceStep(
        "repository_validation",
        ("python3", "scripts/validate_repository.py"),
        "documentation",
    ),
    AssuranceStep("workflow_lint", ("make", "lint-workflows"), "security"),
    AssuranceStep("shell_lint", ("make", "lint-shell"), "security"),
    AssuranceStep("dockerfile_lint", ("make", "lint-docker"), "security"),
    AssuranceStep("secret_scanning", ("make", "security-secrets"), "security"),
    AssuranceStep("python_security_scan", ("make", "security-python"), "security"),
    AssuranceStep("dependency_scan", ("make", "security-dependencies"), "security"),
    AssuranceStep("sbom_generation", ("make", "generate-sbom"), "security"),
    AssuranceStep("container_contract_validation", ("make", "validate-containers"), "containers"),
    AssuranceStep("release_assurance", ("make", "release-assurance"), "release"),
    AssuranceStep(
        "offline_lifecycle_orchestration",
        (
            "python3",
            "-m",
            "ml_product.cli",
            "lifecycle-run-end-to-end",
            "--mode",
            "local_safe",
            "--json",
        ),
        "lifecycle",
    ),
    AssuranceStep(
        "lifecycle_evidence_checksum",
        ("python3", "-m", "ml_product.cli", "lifecycle-validate-workflow-evidence"),
        "lifecycle",
    ),
    AssuranceStep(
        "lifecycle_resume",
        ("python3", "-m", "ml_product.cli", "lifecycle-resume-workflow", "--json"),
        "lifecycle",
    ),
]

OPTIONAL_LIVE_STEPS = [
    AssuranceStep("postgresql_readiness", ("make", "postgres-ready"), "optional_live"),
    AssuranceStep("postgresql_validation", ("make", "postgres-validate"), "optional_live"),
    AssuranceStep("denodo_readiness", ("make", "denodo-ready"), "optional_live"),
    AssuranceStep("denodo_view_listing", ("make", "denodo-list-views"), "optional_live"),
    AssuranceStep(
        "denodo_postgresql_population_compare",
        ("make", "denodo-compare-postgresql"),
        "optional_live",
    ),
]

OPTIONAL_CONTAINER_STEPS = [
    AssuranceStep("container_build", ("make", "build-containers"), "optional_containers"),
    AssuranceStep(
        "local_deployment_smoke",
        ("make", "smoke-test-local-deployment"),
        "optional_containers",
    ),
]

OPTIONAL_R_STEPS = [
    AssuranceStep("r_dependency_restore", ("make", "restore-r"), "optional_r"),
    AssuranceStep("r_tests", ("make", "test-r"), "optional_r"),
    AssuranceStep("rshiny_validation", ("make", "validate-rshiny"), "optional_r"),
]


def main() -> int:
    args = parse_args()
    steps = list(MANDATORY_STEPS)
    if args.include_live:
        steps.extend(OPTIONAL_LIVE_STEPS)
    if args.include_containers:
        steps.extend(OPTIONAL_CONTAINER_STEPS)
    if args.include_r:
        steps.extend(OPTIONAL_R_STEPS)

    if args.plan:
        print(json.dumps(_plan_payload(steps), indent=2, sort_keys=True))
        return 0

    _write_report(_provisional_report(include_live=args.include_live), args.output)
    results = []
    for step in steps:
        _cleanup_disposable_artifacts()
        results.append(_run_step(step))
        _cleanup_disposable_artifacts()
    report = _build_report(results, include_live=args.include_live)
    _write_report(report, args.output)
    _print_summary(report)
    return 0 if report["overall_outcome"] == "passed" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-live",
        action="store_true",
        help="Run optional PostgreSQL and Denodo live checks.",
    )
    parser.add_argument(
        "--include-containers",
        action="store_true",
        help="Build images and run the local deployment smoke test.",
    )
    parser.add_argument(
        "--include-r",
        action="store_true",
        help="Run R dependency restore and R/Shiny tests.",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Print the command plan without executing assurance steps.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPORT_PATH,
        help="Report output path.",
    )
    return parser.parse_args()


def _plan_payload(steps: list[AssuranceStep]) -> dict[str, Any]:
    return {
        "schema_version": "final-assurance-plan/v1",
        "offline_safe_by_default": True,
        "requires_credentials": False,
        "steps": [
            {
                "name": step.name,
                "category": step.category,
                "command": list(step.command),
                "required": step.required,
            }
            for step in steps
        ],
        "optional_groups": {
            "live_integrations": [step.name for step in OPTIONAL_LIVE_STEPS],
            "containers": [step.name for step in OPTIONAL_CONTAINER_STEPS],
            "r": [step.name for step in OPTIONAL_R_STEPS],
        },
    }


def _provisional_report(*, include_live: bool) -> dict[str, Any]:
    return {
        "schema_version": "final-assurance-report/v1",
        "repository": "enterprise-rshiny-ml-product-delivery-platform",
        "repository_commit": _git_commit(),
        "offline_safe_by_default": True,
        "credentials_required": False,
        "environment": _environment_summary(),
        "reconstruction": {
            "canonical_command": "make build-review-artifacts",
            "status": "not_run",
        },
        "steps": [],
        "documentation_validation": {"status": "not_run", "checks": []},
        "security_results": {"status": "not_run", "steps": []},
        "container_results": {"status": "not_run", "steps": []},
        "lifecycle_orchestration": {
            "status": "not_run",
            "mutation_flags": {
                "active_model_changed": False,
                "local_activation_performed": False,
                "local_registry_mutated": False,
            },
        },
        "release_readiness": _release_readiness_summary(),
        "optional_live_integrations": {
            "included": include_live,
            "postgresql": "not_run" if not include_live else "see_steps",
            "denodo": "not_run" if not include_live else "see_steps",
            "sas_viya": "requires_external_environment",
        },
        "known_limitations": [
            "Synthetic data only; no clinical deployment claim.",
            "Live SAS Viya registration and promotion require an external environment.",
            "Operational release remains blocked until approval and activation are granted.",
        ],
        "overall_outcome": "not_run",
        "failed_required_steps": ["final_assurance_in_progress"],
    }


def _run_step(step: AssuranceStep) -> dict[str, Any]:
    completed = subprocess.run(
        step.command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    result: dict[str, Any] = {
        "name": step.name,
        "category": step.category,
        "command": list(step.command),
        "required": step.required,
        "returncode": completed.returncode,
        "status": "passed" if completed.returncode == 0 else "failed",
        "stdout_summary": _summarise(completed.stdout),
        "stderr_summary": _summarise(completed.stderr),
    }
    if step.category == "lifecycle":
        payload = _first_json_object(completed.stdout)
        if payload:
            result["stdout_json"] = _lifecycle_payload_summary(payload)
    return result


def _cleanup_disposable_artifacts() -> None:
    for path in DISPOSABLE_ARTIFACTS:
        path.unlink(missing_ok=True)
    for path in ROOT.glob(".coverage.*"):
        if path.is_file():
            path.unlink()


def _lifecycle_payload_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": payload.get("mode"),
        "workflow_id": payload.get("workflow_id"),
        "configuration_fingerprint": payload.get("configuration_fingerprint"),
        "package_fingerprint": payload.get("package_fingerprint"),
        "evidence_checksum": payload.get("evidence_checksum"),
        "summary": payload.get("summary"),
        "mutation_flags": payload.get("mutation_flags"),
    }


def _build_report(results: list[dict[str, Any]], *, include_live: bool) -> dict[str, Any]:
    required_failed = [
        result["name"]
        for result in results
        if result["required"] and result["status"] != "passed"
    ]
    lifecycle_result = _lifecycle_result(results)
    if lifecycle_result.get("summary_status") == "failed":
        required_failed.append("offline_lifecycle_orchestration")
    return {
        "schema_version": "final-assurance-report/v1",
        "repository": "enterprise-rshiny-ml-product-delivery-platform",
        "repository_commit": _git_commit(),
        "offline_safe_by_default": True,
        "credentials_required": False,
        "environment": _environment_summary(),
        "reconstruction": {
            "canonical_command": "make build-review-artifacts",
            "status": _status_for(results, "clean_checkout_review_artifact_reconstruction"),
        },
        "steps": results,
        "documentation_validation": {
            "status": _status_for(results, "repository_validation"),
            "checks": [
                "README links",
                "architecture diagram source",
                "evidence-index paths",
                "synthetic-data disclosure",
                "SAS Viya limitations",
                "promotion versus activation distinction",
            ],
        },
        "security_results": _category_summary(results, "security"),
        "container_results": _category_summary(results, "containers"),
        "lifecycle_orchestration": lifecycle_result,
        "release_readiness": _release_readiness_summary(),
        "optional_live_integrations": {
            "included": include_live,
            "postgresql": "not_run" if not include_live else "see_steps",
            "denodo": "not_run" if not include_live else "see_steps",
            "sas_viya": "requires_external_environment",
        },
        "known_limitations": [
            "Synthetic data only; no clinical deployment claim.",
            "Live SAS Viya registration and promotion require an external environment.",
            "Operational release remains blocked until approval and activation are granted.",
            "Specialist security tools may be unavailable locally and are recorded honestly.",
        ],
        "overall_outcome": "failed" if required_failed else "passed",
        "failed_required_steps": sorted(set(required_failed)),
    }


def _lifecycle_result(results: list[dict[str, Any]]) -> dict[str, Any]:
    step = next(
        (result for result in results if result["name"] == "offline_lifecycle_orchestration"),
        None,
    )
    if step is None:
        return {"status": "not_run"}
    payload = step.get("stdout_json")
    if not isinstance(payload, dict):
        payload = _first_json_object(step["stdout_summary"])
    summary = payload.get("summary") if isinstance(payload, dict) else None
    mutation_flags = payload.get("mutation_flags") if isinstance(payload, dict) else None
    return {
        "status": step["status"],
        "summary_status": None if not isinstance(summary, dict) else summary.get("status"),
        "blocked_not_failed": isinstance(summary, dict) and summary.get("status") == "blocked",
        "mutation_flags": mutation_flags,
        "evidence_checksum_status": _status_for(results, "lifecycle_evidence_checksum"),
        "resume_status": _status_for(results, "lifecycle_resume"),
    }


def _release_readiness_summary() -> dict[str, Any]:
    path = ROOT / "reports" / "assurance" / "release_readiness.json"
    if not path.is_file():
        return {"status": "missing"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "local_review_readiness": payload.get("local_review_readiness"),
        "operational_release_readiness": payload.get("operational_release_readiness"),
        "model_approval_state": payload.get("model_approval_state"),
        "model_activation_state": payload.get("model_activation_state"),
        "external_deployment_state": payload.get("external_deployment_state"),
    }


def _category_summary(results: list[dict[str, Any]], category: str) -> dict[str, Any]:
    matching = [result for result in results if result["category"] == category]
    return {
        "status": "passed"
        if matching and all(result["status"] == "passed" for result in matching)
        else "not_run"
        if not matching
        else "failed",
        "steps": [result["name"] for result in matching],
    }


def _status_for(results: list[dict[str, Any]], name: str) -> str:
    for result in results:
        if result["name"] == name:
            return str(result["status"])
    return "not_run"


def _environment_summary() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "ruff": _tool_version(("python3", "-m", "ruff", "--version")),
        "mypy": _tool_version(("python3", "-m", "mypy", "--version")),
        "pytest": _tool_version(("python3", "-m", "pytest", "--version")),
        "rscript_available": shutil.which("Rscript") is not None,
        "docker_available": shutil.which("docker") is not None,
        "bandit_available": shutil.which("bandit") is not None,
        "pip_audit_available": shutil.which("pip-audit") is not None,
        "trivy_available": shutil.which("trivy") is not None,
    }


def _tool_version(command: tuple[str, ...]) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return "not_available"
    return _summarise(completed.stdout or completed.stderr, max_lines=1)


def _git_commit() -> str:
    completed = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unavailable"


def _summarise(text: str, *, max_lines: int = 12) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return _sanitize_text("\n".join(lines[-max_lines:]))


def _sanitize_text(text: str) -> str:
    sanitized = text.replace(str(ROOT), ".")
    sanitized = re.sub(r"/Users/[^\s:]+(?:/[^\s:]+)*", "<user-path>", sanitized)
    sanitized = re.sub(
        r"/Library/Frameworks/[^\s:]+(?:/[^\s:]+)*",
        "<system-python-path>",
        sanitized,
    )
    return sanitized


def _first_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_report(report: dict[str, Any], path: Path) -> None:
    output = path if path.is_absolute() else ROOT / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _print_summary(report: dict[str, Any]) -> None:
    print(
        f"final-assurance {report['overall_outcome']}: "
        f"failed_required_steps={report['failed_required_steps']}"
    )
    print(f"report={REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    raise SystemExit(main())
