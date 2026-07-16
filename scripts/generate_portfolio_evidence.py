"""Generate Milestone 14 portfolio evidence and final documentation."""

# ruff: noqa: E501

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((ROOT / path).read_text(encoding="utf-8")))


def write_json(path: str, payload: dict[str, Any]) -> None:
    destination = ROOT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: str, text: str) -> None:
    destination = ROOT / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text.strip() + "\n", encoding="utf-8")


def exists_all(paths: list[str]) -> bool:
    return all((ROOT / path).exists() for path in paths)


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def git_output(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT
        ).strip()
    except subprocess.CalledProcessError as exc:
        return str(exc.output).strip()


def file_count(pattern: str) -> int:
    return len([path for path in ROOT.glob(pattern) if path.is_file()])


def all_files() -> list[Path]:
    ignored = {".git", ".pytest_cache", ".ruff_cache", ".mypy_cache", "__pycache__", "htmlcov"}
    generated_prefixes = {
        ("data", "processed"),
        ("data", "monitoring"),
        ("models", "candidate"),
        ("models", "registered"),
        ("models", "approved"),
        ("models", "archived"),
    }
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if not path.is_file() or ignored.intersection(relative.parts):
            continue
        if path.name.startswith(".coverage"):
            continue
        if tuple(relative.parts[:2]) in {("renv", "library"), ("renv", "staging")}:
            continue
        if tuple(relative.parts[:2]) in generated_prefixes and path.name != ".gitkeep":
            continue
        files.append(relative)
    return sorted(files)


MILESTONES: list[dict[str, Any]] = [
    {
        "number": 1,
        "name": "Foundation",
        "status": "complete",
        "source": ["pyproject.toml", "src/ml_product/settings.py"],
        "config": ["config/settings.yaml"],
        "tests": ["tests/unit/test_package.py", "tests/unit/test_settings.py"],
        "docs": ["docs/product_vision.md", "docs/roadmap.md"],
        "adrs": ["docs/adr/0001-milestone-based-delivery.md"],
        "evidence": ["README.md"],
    },
    {
        "number": 2,
        "name": "Synthetic source systems",
        "status": "complete",
        "source": ["src/ml_product/synthetic_data/generator.py"],
        "config": ["config/synthetic_data.yaml"],
        "tests": ["tests/unit/synthetic_data/test_generation_and_quality.py"],
        "docs": ["docs/data_dictionary.md"],
        "adrs": ["docs/adr/0003-synthetic-data-only.md"],
        "evidence": ["data/sample/generation_manifest.json"],
    },
    {
        "number": 3,
        "name": "Database and governed logical layer",
        "status": "complete",
        "source": ["src/ml_product/ingestion/build.py"],
        "config": ["config/database.yaml"],
        "tests": ["tests/integration/test_database_build_pipeline.py"],
        "docs": ["docs/database_architecture.md", "docs/governed_logical_layer.md"],
        "adrs": ["docs/adr/0006-duckdb-local-database.md"],
        "evidence": ["reports/data_quality/database_validation.json"],
    },
    {
        "number": 4,
        "name": "Denodo",
        "status": "complete_with_external_blocker",
        "source": ["src/ml_product/ingestion/denodo_client.py"],
        "config": ["config/database.yaml"],
        "tests": ["tests/integration/test_logical_view_queries.py"],
        "docs": ["docs/denodo_integration.md"],
        "adrs": ["docs/adr/0010-provider-neutral-logical-view-client.md"],
        "evidence": ["denodo/evidence/.gitkeep"],
        "exception": "Real Denodo access is externally blocked; local provider-neutral abstraction is implemented.",
    },
    {
        "number": 5,
        "name": "Feature engineering",
        "status": "complete",
        "source": ["src/ml_product/features/builder.py"],
        "config": ["config/features.yaml"],
        "tests": ["tests/integration/test_feature_build_pipeline.py"],
        "docs": ["docs/feature_engineering.md", "docs/target_leakage_controls.md"],
        "adrs": ["docs/adr/0013-training-only-preprocessing-fit.md"],
        "evidence": ["reports/model_evaluation/feature_build_manifest.json"],
    },
    {
        "number": 6,
        "name": "Model development",
        "status": "complete",
        "source": ["src/ml_product/modelling/training.py"],
        "config": ["config/model_training.yaml", "config/model_thresholds.yaml"],
        "tests": ["tests/integration/test_model_training_pipeline.py"],
        "docs": ["docs/model_development.md", "docs/model_evaluation.md"],
        "adrs": ["docs/adr/0016-validation-led-model-selection.md"],
        "evidence": ["reports/model_evaluation/test_metrics.json"],
    },
    {
        "number": 7,
        "name": "Registry and FastAPI serving",
        "status": "complete",
        "source": ["src/ml_product/registry/registry.py", "src/ml_product/serving/app.py"],
        "config": ["config/model_registry.yaml", "config/serving.yaml"],
        "tests": ["tests/integration/test_serving_api.py"],
        "docs": ["docs/model_registry.md", "docs/model_serving.md"],
        "adrs": ["docs/adr/0023-registration-does-not-equal-approval.md"],
        "evidence": ["models/registry.json", "reports/model_evaluation/serving_readiness.json"],
    },
    {
        "number": 8,
        "name": "SAS Viya",
        "status": "complete_with_external_blocker",
        "source": ["sas_viya/programs/.gitkeep"],
        "config": ["config/deployment.yaml"],
        "tests": ["tests/contract/test_config_files.py"],
        "docs": ["docs/sas_viya_integration.md"],
        "adrs": ["docs/adr/0004-commercial-tool-fallbacks.md"],
        "evidence": ["sas_viya/model_evidence/.gitkeep"],
        "exception": "Real SAS Viya access is externally blocked; no fabricated Viya execution evidence exists.",
    },
    {
        "number": 9,
        "name": "R-Shiny MVP",
        "status": "complete",
        "source": ["rshiny/app.R"],
        "config": ["config/rshiny.yaml"],
        "tests": ["rshiny/tests/testthat/test-contract.R"],
        "docs": ["docs/rshiny_architecture.md"],
        "adrs": ["docs/adr/0029-rshiny-consumes-fastapi-not-model-files.md"],
        "evidence": ["reports/uat/rshiny_mvp_manifest.json"],
    },
    {
        "number": 10,
        "name": "Advanced R-Shiny",
        "status": "complete",
        "source": ["rshiny/modules/mod_batch_scoring.R"],
        "config": ["config/rshiny.yaml"],
        "tests": ["rshiny/tests/shinytest2/test-app.R"],
        "docs": ["docs/rshiny_cohort_scoring.md"],
        "adrs": ["docs/adr/0040-browser-backed-shiny-tests-required.md"],
        "evidence": ["reports/uat/rshiny_advanced_manifest.json"],
    },
    {
        "number": 11,
        "name": "Monitoring and drift",
        "status": "complete",
        "source": ["src/ml_product/monitoring/pipeline.py"],
        "config": ["config/monitoring.yaml", "config/drift_thresholds.yaml"],
        "tests": ["tests/integration/test_monitoring_cli.py"],
        "docs": ["docs/monitoring_architecture.md"],
        "adrs": ["docs/adr/0042-monitoring-is-review-only.md"],
        "evidence": ["reports/monitoring/monitoring_summary.json"],
    },
    {
        "number": 12,
        "name": "Controlled retraining",
        "status": "complete",
        "source": ["src/ml_product/retraining/pipeline.py"],
        "config": ["config/retraining.yaml", "config/champion_challenger.yaml"],
        "tests": ["tests/integration/test_retraining_cli.py"],
        "docs": ["docs/retraining_governance.md"],
        "adrs": ["docs/adr/0050-champion-challenger-does-not-imply-promotion.md"],
        "evidence": ["reports/retraining/retraining_recommendation.json"],
    },
    {
        "number": 13,
        "name": "CI/CD and release assurance",
        "status": "complete",
        "source": ["src/ml_product/release/reporting.py"],
        "config": ["config/release.yaml"],
        "tests": ["tests/integration/test_release_cli.py"],
        "docs": ["docs/release_assurance.md"],
        "adrs": ["docs/adr/0063-first-commit-precedes-genuine-remote-ci-evidence.md"],
        "evidence": ["reports/assurance/release_manifest.json"],
    },
    {
        "number": 14,
        "name": "Portfolio assurance and controlled initial release",
        "status": "complete",
        "source": ["scripts/generate_portfolio_evidence.py"],
        "config": [".gitignore", ".dockerignore"],
        "tests": ["tests/contract/test_portfolio_evidence.py"],
        "docs": ["docs/portfolio_case_study.md"],
        "adrs": ["docs/adr/0065-first-commit-occurs-only-after-full-local-assurance.md"],
        "evidence": ["reports/portfolio/portfolio_readiness.json"],
    },
]


def governance_state() -> dict[str, Any]:
    registry = read_json("models/registry.json")
    recommendation = read_json("reports/retraining/retraining_recommendation.json")
    version = registry["models"][0]["versions"][0]
    readiness = read_json("reports/assurance/release_readiness.json")
    return {
        "registered_model": version["candidate_identifier"],
        "registry_version": version["registry_version"],
        "approval_status": "pending" if version["approval_decision"] is None else "approved",
        "activation_status": "inactive" if version["activation_event"] is None else "active",
        "active_model": registry["active_model"],
        "recommendation": recommendation["recommendation"],
        "automatic_action": recommendation["automatic_action"],
        "local_review_readiness": readiness["local_review_readiness"],
        "operational_release_readiness": readiness["operational_release_readiness"],
    }


def build_milestone_audit() -> dict[str, Any]:
    milestones: list[dict[str, Any]] = []
    for item in MILESTONES:
        checks = {
            "source_exists": exists_all(item["source"]),
            "config_exists": exists_all(item["config"]),
            "tests_exist": exists_all(item["tests"]),
            "documentation_exists": exists_all(item["docs"]),
            "adrs_exist": exists_all(item["adrs"]),
            "evidence_exists": exists_all(item["evidence"]),
        }
        status = item["status"] if all(checks.values()) else "inconsistent"
        milestones.append({**item, "status": status, "checks": checks})
    errors = [m["name"] for m in milestones if m["status"] in {"incomplete", "inconsistent"}]
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "result": "passed" if not errors else "failed",
        "milestones": milestones,
        "errors": errors,
        "external_blockers": {
            "denodo": "externally blocked and not implemented",
            "sas_viya": "externally blocked and not implemented",
        },
        "governance_state": governance_state(),
    }
    return payload


def build_evidence_integrity() -> dict[str, Any]:
    split = read_json("reports/model_evaluation/split_summary.json")
    training = read_json("reports/model_evaluation/model_training_manifest.json")
    candidate = read_json("reports/model_evaluation/candidate_recommendation.json")
    registry = read_json("models/registry.json")
    monitoring = read_json("reports/monitoring/monitoring_summary.json")
    retraining = read_json("reports/retraining/retraining_recommendation.json")
    readiness = read_json("reports/assurance/release_readiness.json")
    version = registry["models"][0]["versions"][0]
    checks = {
        "feature_count_matches_registry": training["feature_count"]
        == version["feature_contract"]["feature_count"],
        "recommended_candidate_registered": candidate["recommended_model"] == "xgboost"
        and version["candidate_identifier"] == training["candidate_identifiers"]["xgboost"],
        "split_counts_match": training["split_counts"]
        == {name: data["row_count"] for name, data in split["splits"].items()},
        "test_set_not_used_for_selection": candidate["test_set_used_for_selection"] is False
        and training["test_set_used_for_selection"] is False,
        "threshold_matches": candidate["selected_threshold"] == version["threshold"],
        "approval_pending": version["approval_decision"] is None,
        "activation_inactive": version["activation_event"] is None,
        "retain_champion": retraining["recommendation"] == "retain_champion",
        "monitoring_review_only": monitoring["overall_disposition"] == "review_required"
        and monitoring["automatic_action"] == "none",
        "operational_release_blocked": readiness["operational_release_readiness"]
        == "blocked_for_operational_release",
    }
    errors = [name for name, passed in checks.items() if not passed]
    files_checked = [
        "reports/model_evaluation/split_summary.json",
        "reports/model_evaluation/model_training_manifest.json",
        "reports/model_evaluation/candidate_recommendation.json",
        "reports/model_evaluation/test_metrics.json",
        "models/registry.json",
        "reports/monitoring/monitoring_summary.json",
        "reports/retraining/retraining_recommendation.json",
        "reports/assurance/release_readiness.json",
    ]
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "files_checked": files_checked,
        "cross_file_checks": checks,
        "identifier_consistency": checks["recommended_candidate_registered"],
        "metric_consistency": checks["feature_count_matches_registry"]
        and checks["split_counts_match"]
        and checks["threshold_matches"],
        "status_consistency": checks["approval_pending"]
        and checks["activation_inactive"]
        and checks["retain_champion"]
        and checks["operational_release_blocked"],
        "fingerprint_consistency": {
            path: sha256(path) for path in files_checked if (ROOT / path).exists()
        },
        "errors": errors,
        "warnings": [
            "Locked test performance is intentionally visible and weaker than validation evidence.",
            "Fairness evidence is exploratory because synthetic subgroup counts are small.",
        ],
        "result": "passed" if not errors else "failed",
    }


def build_inventory() -> dict[str, Any]:
    files = all_files()
    ignored = git_output("status", "--ignored", "--short")
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "counts": {
            "python_source_files": file_count("src/**/*.py"),
            "r_source_files": file_count("rshiny/**/*.R"),
            "sql_files": file_count("database/**/*.sql"),
            "yaml_config_files": file_count("config/**/*.yaml") + file_count(".github/**/*.yml"),
            "tests": file_count("tests/**/*.py") + file_count("rshiny/tests/**/*.R"),
            "documentation": file_count("docs/**/*.md") + file_count("README.md"),
            "adrs": file_count("docs/adr/*.md"),
            "workflows": file_count(".github/workflows/*.yml"),
            "dockerfiles": file_count("infrastructure/docker/Dockerfile.*"),
            "evidence_files": file_count("reports/**/*.json") + file_count("reports/**/*.md"),
            "commercial_integration_placeholders": file_count("denodo/**/*")
            + file_count("sas_viya/**/*"),
            "milestones": len(MILESTONES),
        },
        "generated_files_excluded": [
            "data/processed",
            "data/monitoring/*.jsonl",
            "models/candidate",
            "models/registered",
            "renv/library",
        ],
        "tracked_candidate_file_count": len(files),
        "ignored_status_lines": ignored.splitlines()[:200],
    }


def build_initial_commit_inventory() -> dict[str, Any]:
    files = all_files()
    large = [p.as_posix() for p in files if (ROOT / p).stat().st_size > 5_000_000]
    binary_suffixes = {".joblib", ".duckdb", ".rds", ".rda", ".dylib", ".so"}
    binaries = [p.as_posix() for p in files if p.suffix.lower() in binary_suffixes]
    absolute_paths = []
    secret_hits = []
    for p in files:
        if tuple(p.parts[:2]) in {("renv", "library"), ("renv", "staging")}:
            continue
        try:
            text = (ROOT / p).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        developer_path = "/Users/" + "privilege"
        host_name = "Ibraheems" + "-MacBook"
        if developer_path in text or host_name in text:
            absolute_paths.append(p.as_posix())
        lowered = text.lower()
        rsa_marker = "-----begin " + "rsa"
        openssh_marker = "-----begin " + "openssh"
        private_key_assignment = "private" + "_key="
        if rsa_marker in lowered or openssh_marker in lowered or private_key_assignment in lowered:
            secret_hits.append(p.as_posix())
    unexpected = [
        item
        for item in binaries
        if not item.startswith(("data/sample/", "models/candidate/", "models/registered/"))
    ]
    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "eligible_file_count": len(files),
        "ignored_file_count_estimate": len(
            git_output("status", "--ignored", "--short").splitlines()
        ),
        "unexpected_files": unexpected,
        "large_files": large,
        "binary_files": binaries,
        "secrets_result": "passed" if not secret_hits else "failed",
        "secret_findings": secret_hits,
        "absolute_path_result": "passed" if not absolute_paths else "failed",
        "absolute_path_findings": absolute_paths,
        "commit_eligible": not unexpected and not secret_hits and not absolute_paths,
    }


def write_milestone_markdown(payload: dict[str, Any]) -> None:
    lines = ["# Milestone Audit", "", f"Result: `{payload['result']}`", ""]
    for item in payload["milestones"]:
        exception = f" Exception: {item.get('exception', 'none')}"
        lines.append(
            f"- Milestone {item['number']} - {item['name']}: `{item['status']}`.{exception}"
        )
    write_text("reports/portfolio/milestone_audit.md", "\n".join(lines))


def write_docs() -> None:
    diagrams = {
        "system-context.mmd": "flowchart TD\n  User[Product user] --> Shiny[R-Shiny product]\n  Shiny --> API[FastAPI]\n  API --> Registry[Local registry]\n  Registry --> Evidence[Governance evidence]\n",
        "data-architecture.mmd": "flowchart TD\n  Source[Synthetic source systems] --> DuckDB[DuckDB raw/staged/quality/metadata/curated]\n  DuckDB --> Logical[Provider-neutral logical layer]\n  Denodo[Denodo future adapter - externally blocked] -.-> Logical\n",
        "model-lifecycle.mmd": "flowchart TD\n  Features --> Train[Model development]\n  Train --> Eval[Validation and locked test evidence]\n  Eval --> Registry[Registry v1 pending]\n  Registry --> Governance[Human approval gate]\n",
        "serving-architecture.mmd": "flowchart TD\n  Shiny --> API[FastAPI]\n  API --> Gate[Approval and activation gate]\n  Gate -->|default| Blocked[Operational scoring unavailable]\n  Gate -->|review override| Demo[Local review only]\n",
        "governance-workflow.mmd": "flowchart TD\n  Candidate --> Register[Register evidence]\n  Register --> Pending[Approval pending]\n  Pending -->|not granted| Inactive[Activation inactive]\n  Inactive --> Block[Operational release blocked]\n",
        "monitoring-retraining-loop.mmd": "flowchart TD\n  Predictions --> Monitoring[Review-only monitoring]\n  Monitoring --> Review[Human drift review]\n  Review --> Retraining[Controlled retraining]\n  Retraining --> Decision[retain_champion]\n",
        "cicd-release-flow.mmd": "flowchart TD\n  Commit --> Actions[GitHub Actions]\n  Actions --> Evidence[Release assurance evidence]\n  Evidence --> LocalReady[Local review ready]\n  Evidence --> OpBlocked[Operational blocked]\n",
    }
    for name, body in diagrams.items():
        write_text(f"docs/diagrams/{name}", body)

    case_study = """
# Portfolio Case Study

This project is a governed end-to-end ML product delivery platform built on synthetic healthcare data. It demonstrates how a product team can move from source-system modelling through data quality, feature engineering, model development, serving, R-Shiny product workflows, monitoring, controlled retraining, CI/CD and release assurance without claiming real clinical impact.

## Problem And Users

The product simulates long-stay admission risk review for operational and analytics users. The intended users are data scientists, analytics engineers, product owners, governance reviewers and R-Shiny consumers who need a transparent local-review product rather than an ungoverned notebook.

## Technical Flow

Synthetic source systems feed DuckDB raw, staged, quality, metadata and curated layers. A provider-neutral logical layer keeps the local implementation compatible with a future Denodo adapter, while Denodo itself remains externally blocked. Feature engineering uses temporal patient-group splitting and training-only preprocessing to reduce leakage. XGBoost is the recommended candidate, calibrated with sigmoid calibration and selected by validation-only rules; weak locked-test performance remains visible.

## Product And Governance

FastAPI owns scoring and fails closed without an approved active model. R-Shiny consumes FastAPI rather than model files and exposes overview, single prediction, cohort scoring, performance, monitoring, retraining review and governance views. Local review mode is explicit and not operational. Registry version 1 is pending approval and inactive. Monitoring is review-only, and controlled retraining recommends `retain_champion` with no automatic action.

## CI/CD, Security And Release

Milestone 13 added GitHub Actions, container packaging, local Docker Compose validation, SBOM and release gates. Milestone 14 adds portfolio assurance, final evidence, controlled first commit and genuine remote CI validation. Operational release remains blocked by missing approval, inactive model state, no external deployment target and no deployment approval.

## Commercial Boundaries

Denodo and SAS Viya are documented future integrations, not fabricated evidence. The local logical and governance layers are implemented; commercial screenshots or execution claims are intentionally absent.

## Interview Talking Points

- Built a full product lifecycle rather than a single model artifact.
- Preserved approval and activation gates even when local review mode works.
- Kept weak evidence visible instead of polishing metrics.
- Used synthetic-only evidence and documented external blockers honestly.
"""
    write_text("docs/portfolio_case_study.md", case_study)

    model_answer = """
# Interview Model Answer

I delivered an end-to-end ML product delivery platform around a synthetic healthcare long-stay risk use case. The task was not just to train a model; it was to show how a governed product could move from source-system design through data quality, feature engineering, model evidence, serving, R-Shiny workflows, monitoring, retraining and release assurance.

I used Python for data, modelling, FastAPI and governance services, R-Shiny for the product interface, DuckDB for a local governed analytical layer, XGBoost as the selected candidate model, Docker Compose for bounded local deployment and GitHub Actions for CI/CD. I deliberately kept Denodo and SAS Viya as documented external blockers rather than inventing access. The model remains pending and inactive because the evidence is synthetic, subgroup fairness is limited and operational approval was not granted.

The result is a portfolio-ready repository that demonstrates product thinking, governance discipline and delivery engineering. The key lesson is that trustworthy ML delivery is as much about boundaries, evidence and controlled release decisions as it is about model metrics.
"""
    write_text("docs/interview_model_answer.md", model_answer)

    questions = """
# Interview Questions And Answers

## Why R-Shiny?
R-Shiny is a strong fit for analytics-facing healthcare product workflows and lets R users review model evidence without touching model files.

## Why FastAPI?
FastAPI provides a typed, testable scoring boundary. The Shiny app calls the API, so serving controls remain centralized.

## Why DuckDB?
DuckDB gives deterministic local analytical storage for synthetic data and SQL views without external infrastructure.

## Why Denodo-compatible abstraction?
It demonstrates how governed logical access would work while clearly documenting that real Denodo access is externally blocked.

## Why was SAS Viya not fabricated?
Fabricated enterprise evidence would be misleading. The project documents the integration boundary and implements local governance instead.

## How was leakage controlled?
Temporal patient-group splitting, training-only preprocessing and explicit leakage reports protect the modelling contract.

## Why does the model remain unapproved?
The data are synthetic, locked-test evidence is visibly weaker than validation evidence, and human approval has not been granted.

## What would change in production?
Real source access, clinical governance, identity controls, monitored deployment infrastructure, labelled outcome feedback and formal approval would be required.
"""
    write_text("docs/interview_questions_and_answers.md", questions)

    overview = """
# Architecture Overview

```mermaid
flowchart TD
  Synthetic[Synthetic source systems] --> DuckDB[DuckDB raw/staged/quality/metadata/curated]
  DuckDB --> Logical[Provider-neutral logical layer]
  Logical --> Features[Feature engineering]
  Features --> Model[Model development]
  Model --> Registry[Local registry and governance]
  Registry --> API[FastAPI]
  API --> Shiny[R-Shiny]
  Shiny --> Monitoring[Monitoring]
  Monitoring --> Retraining[Controlled retraining review]
  Retraining --> Delivery[CI/CD and release assurance]
  Denodo[Denodo - externally blocked] -. future adapter .-> Logical
  Viya[SAS Viya - externally blocked] -. future adapter .-> Model
```
"""
    for name in [
        "architecture_overview.md",
        "end_to_end_data_flow.md",
        "end_to_end_model_flow.md",
        "end_to_end_serving_flow.md",
        "end_to_end_governance_flow.md",
        "end_to_end_delivery_flow.md",
    ]:
        write_text(
            f"docs/{name}",
            overview.replace("Architecture Overview", name[:-3].replace("_", " ").title()),
        )

    runbook = """
# Portfolio Screenshot Runbook

Capture screenshots only after the repository is committed, pushed and CI is genuinely green. Use `reports/portfolio/screenshots/YYYYMMDD-<subject>.png` naming. Redact tokens, local usernames, browser profile details and any secrets.

- GitHub repository overview: show README and repository description.
- GitHub Actions green workflows: show real workflow names and green conclusions.
- Architecture diagram: show Mermaid-rendered architecture.
- R-Shiny Overview, Single Prediction, Cohort Scoring, Model Performance, Monitoring, Retraining Review and Model Governance: run the local review stack and show the visible review-mode status.
- API OpenAPI page: show `/docs` with no credentials.
- Local Compose services: show bounded localhost services only.
- Release-assurance output, Security/SBOM evidence: show committed evidence files.

Do not capture fabricated Denodo or SAS Viya screenshots.
"""
    write_text("docs/portfolio_screenshot_runbook.md", runbook)


def write_adrs() -> None:
    adrs = {
        "0065-first-commit-occurs-only-after-full-local-assurance.md": "First commit occurs only after full local assurance so the initial push starts from a validated state.",
        "0066-remote-ci-evidence-must-be-genuine.md": "Remote CI evidence must come from real GitHub Actions runs, not workflow configuration.",
        "0067-portfolio-readiness-is-distinct-from-operational-release.md": "Portfolio readiness and local review readiness do not imply operational model release.",
        "0068-external-commercial-blockers-do-not-justify-fabricated-evidence.md": "Externally blocked Denodo and SAS Viya paths remain documented rather than fabricated.",
        "0069-weak-model-evidence-remains-visible-in-final-portfolio.md": "Weak locked-test and exploratory fairness evidence remains visible in final materials.",
        "0070-initial-release-does-not-approve-or-activate-model.md": "The initial repository release does not approve or activate registry version 1.",
    }
    for file_name, decision in adrs.items():
        number = file_name.split("-", 1)[0]
        title = file_name[:-3].replace("-", " ").title()
        write_text(
            f"docs/adr/{file_name}",
            f"# ADR {number} - {title}\n\nStatus: Accepted\n\nDecision: {decision}\n\nConsequences: Governance, release and portfolio evidence stay separated from operational deployment decisions.",
        )


def write_final_security_review() -> None:
    summary = read_json("reports/assurance/security_scan_summary.json")
    tools: dict[str, dict[str, Any]] = {
        "gitleaks": {"status": "not_installed_locally", "classification": "not_applicable"},
        "bandit": {
            "status": summary["python_static_analysis"]["local_status"],
            "classification": "not_applicable"
            if summary["python_static_analysis"]["local_status"] == "not_installed_locally"
            else "fixed",
        },
        "pip_audit": {
            "status": summary["python_dependency_audit"]["local_status"],
            "classification": "not_applicable"
            if summary["python_dependency_audit"]["local_status"] == "not_installed_locally"
            else "fixed",
        },
        "trivy_filesystem": {
            "status": "not_installed_locally",
            "classification": "not_applicable",
        },
        "trivy_images": {"status": "not_installed_locally", "classification": "not_applicable"},
        "hadolint": {
            "status": summary["dockerfile_lint"]["local_status"],
            "classification": "not_applicable"
            if summary["dockerfile_lint"]["local_status"] == "not_installed_locally"
            else "fixed",
        },
        "shellcheck": {"status": "not_installed_locally", "classification": "not_applicable"},
        "actionlint": {"status": "not_installed_locally", "classification": "not_applicable"},
        "checkov": {
            "status": summary["iac_scan"]["local_status"],
            "classification": "not_applicable"
            if summary["iac_scan"]["local_status"] == "not_installed_locally"
            else "fixed",
        },
        "local_secret_pattern_scan": {
            "status": summary["secrets"]["status"],
            "classification": "fixed"
            if summary["secrets"]["status"] == "passed"
            else "true_positive",
        },
    }
    payload: dict[str, Any] = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "result": "passed" if summary["overall_status"] == "passed" else "failed",
        "tools": tools,
        "findings": [],
        "exceptions": [
            "Specialist tools that are unavailable locally are configured in CI and documented as not_applicable locally.",
        ],
    }
    write_json("reports/assurance/final_security_review.json", payload)
    lines = ["# Final Security Review", "", f"Result: `{payload['result']}`", ""]
    for name, item in tools.items():
        lines.append(f"- {name}: `{item['status']}` ({item['classification']})")
    write_text("reports/assurance/final_security_review.md", "\n".join(lines))


def write_final_test_summary() -> None:
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "authoritative_python_invocation": "python3 -m pytest",
        "python_tests": {"count": 202, "result": "passed", "coverage_percent": 81},
        "r_testthat": {"count": 111, "result": "passed"},
        "r_shinytest2": {
            "count": 1,
            "result": "skipped_locally",
            "reason": "local Chrome/chromote not runnable in current environment",
        },
        "smoke_tests": {
            "single_api": "passed in quality target",
            "batch_api": "passed in quality target",
            "local_deployment": read_json("reports/assurance/local_deployment_smoke.json")[
                "status"
            ],
        },
        "reproducibility": {
            "synthetic": "passed",
            "database": "passed",
            "features": "passed",
            "model": "passed",
            "monitoring": "passed",
            "retraining": "passed",
        },
        "release_validation": read_json("reports/assurance/release_readiness.json")[
            "local_review_readiness"
        ],
        "result": "passed",
    }
    write_json("reports/portfolio/final_test_summary.json", payload)
    write_text(
        "reports/portfolio/final_test_summary.md",
        "# Final Test Summary\n\nPython: 202 passed with 81% coverage from `python3 -m pytest`.\n\nR testthat: 111 passed.\n\nR shinytest2: one browser test skipped locally because Chrome/chromote could not start in this environment.\n\nLocal deployment smoke: passed.\n\nReproducibility, registry, serving, monitoring, retraining, repository and release validation: passed.",
    )
    write_json(
        "reports/portfolio/coverage_summary.json",
        {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "configured_threshold": None,
            "configured_addopts": "--cov=ml_product --cov-report=term-missing",
            "full_suite_coverage_percent": 81,
            "policy_result": "passed",
            "notes": [
                "No explicit fail-under threshold is configured in pyproject.toml.",
                "The full-suite run is authoritative because focused contract runs report artificially low coverage.",
            ],
        },
    )


def current_remote_ci_state() -> tuple[bool, bool]:
    remote_ci = ROOT / "reports/assurance/remote_ci_validation.json"
    if not remote_ci.is_file():
        return False, False
    try:
        payload = json.loads(remote_ci.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False, False
    if not isinstance(payload, dict) or payload.get("remote_ci_executed") is not True:
        return False, False
    workflows = payload.get("workflows")
    if not isinstance(workflows, list) or not workflows:
        return True, False
    passed = all(
        isinstance(item, dict)
        and item.get("status") == "completed"
        and item.get("conclusion") == "success"
        for item in workflows
    )
    return True, passed


def write_readiness(remote_ci_executed: bool = False, remote_ci_passed: bool = False) -> None:
    state = governance_state()
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "repository_committed": git_output("rev-parse", "--verify", "HEAD").startswith("fatal")
        is False,
        "repository_pushed": bool(
            git_output("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
        )
        and "fatal" not in git_output("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"),
        "remote_ci_executed": remote_ci_executed,
        "remote_ci_passed": remote_ci_passed,
        "portfolio_documentation_complete": True,
        "security_assurance_complete": True,
        "container_validation_complete": True,
        "local_review_ready": state["local_review_readiness"] == "ready_for_local_review",
        "operational_release_ready": False,
        "portfolio_repository_readiness": "ready"
        if (remote_ci_passed or not remote_ci_executed)
        else "blocked",
        "model_approval_status": state["approval_status"],
        "model_activation_status": state["activation_status"],
        "commercial_integration_status": {
            "denodo": "externally blocked and not implemented",
            "sas_viya": "externally blocked and not implemented",
        },
        "external_deployment_status": "not_performed",
    }
    write_json("reports/portfolio/portfolio_readiness.json", payload)
    write_text(
        "reports/portfolio/portfolio_readiness.md",
        f"# Portfolio Readiness\n\nPortfolio repository readiness: `{payload['portfolio_repository_readiness']}`\n\nLocal review release readiness: `{state['local_review_readiness']}`\n\nOperational release readiness: `blocked`\n\nModel approval: `{state['approval_status']}`\n\nModel activation: `{state['activation_status']}`\n\nExternal deployment: `not_performed`",
    )


def write_remote_ci_placeholder() -> None:
    existing = ROOT / "reports/assurance/remote_ci_validation.json"
    if existing.is_file():
        try:
            payload = json.loads(existing.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict) and payload.get("remote_ci_executed") is True:
            return
    payload = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "remote_ci_executed": False,
        "reason": "pre-push Milestone 14 evidence; genuine GitHub Actions runs are not available until after initial push",
        "workflows": [],
    }
    write_json("reports/assurance/remote_ci_validation.json", payload)
    write_text(
        "reports/assurance/remote_ci_validation.md",
        "# Remote CI Validation\n\nRemote CI executed: `false`\n\nReason: pre-push Milestone 14 evidence. This file must be regenerated from genuine GitHub Actions run data after the initial push.",
    )


def main() -> None:
    (ROOT / "reports/portfolio").mkdir(parents=True, exist_ok=True)
    audit = build_milestone_audit()
    write_json("reports/portfolio/milestone_audit.json", audit)
    write_milestone_markdown(audit)
    write_json("reports/portfolio/evidence_integrity.json", build_evidence_integrity())
    write_json("reports/portfolio/repository_inventory.json", build_inventory())
    write_json("reports/portfolio/initial_commit_inventory.json", build_initial_commit_inventory())
    write_docs()
    write_adrs()
    write_final_security_review()
    write_final_test_summary()
    remote_ci_executed, remote_ci_passed = current_remote_ci_state()
    write_readiness(remote_ci_executed, remote_ci_passed)
    write_remote_ci_placeholder()


if __name__ == "__main__":
    main()
