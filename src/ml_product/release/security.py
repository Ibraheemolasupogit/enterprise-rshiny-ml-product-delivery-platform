"""Local security assurance summaries."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(password|secret|token|api[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{24,}"),
]

EXCLUDED_PREFIXES = (
    "renv/library/",
    "renv/cache/",
)


def command_available(name: str) -> bool:
    return shutil.which(name) is not None


def scan_for_secrets(root: Path) -> dict[str, object]:
    findings: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        relative_text = relative.as_posix()
        if any(relative_text.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
            continue
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() in {".joblib", ".parquet", ".duckdb", ".pyc"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(relative_text)
                break
    return {
        "tool": "local_secret_pattern_scan",
        "blocking": True,
        "status": "passed" if not findings else "failed",
        "findings": findings,
    }


def security_summary(root: Path) -> dict[str, object]:
    secrets = scan_for_secrets(root)
    return {
        "secrets": secrets,
        "python_static_analysis": {
            "tool": "bandit",
            "blocking_policy": "high_or_critical_blocks",
            "local_status": "available" if command_available("bandit") else "not_installed_locally",
        },
        "python_dependency_audit": {
            "tool": "pip-audit",
            "blocking_policy": "high_or_critical_blocks_or_document_exception",
            "local_status": "available"
            if command_available("pip-audit")
            else "not_installed_locally",
        },
        "container_vulnerability_scan": {
            "tool": "trivy",
            "blocking_policy": "critical_or_high_blocks",
            "local_status": "available" if command_available("trivy") else "not_installed_locally",
        },
        "dockerfile_lint": {
            "tool": "hadolint",
            "blocking_policy": "error_or_critical_blocks",
            "local_status": "available"
            if command_available("hadolint")
            else "not_installed_locally",
        },
        "iac_scan": {
            "tool": "checkov",
            "blocking_policy": "critical_blocks",
            "local_status": "available"
            if command_available("checkov")
            else "not_installed_locally",
        },
        "overall_status": secrets["status"],
        "limitations": [
            "Specialist security tools run in CI workflows when dependencies are installed.",
            "Local summary records missing tools instead of fabricating scan results.",
        ],
    }
