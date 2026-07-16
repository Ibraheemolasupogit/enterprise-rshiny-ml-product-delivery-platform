"""Target-leakage checks for feature engineering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ml_product.features.config import FeatureConfig

PROHIBITED_PATTERNS = (
    "discharge",
    "length_of_stay",
    "long_stay",
    "readmission",
    "outcome",
)


@dataclass(frozen=True)
class LeakageResult:
    valid: bool
    violations: list[dict[str, str]]
    report: dict[str, Any]


def check_leakage(config: FeatureConfig) -> LeakageResult:
    violations: list[dict[str, str]] = []
    explicit = set(config.excluded_predictors) | set(config.identifiers)
    explicit.add(config.prediction_contract.target_column)
    for feature in config.features.predictors:
        if feature in explicit:
            violations.append({"column": feature, "type": "explicit_prohibited"})
        for pattern in PROHIBITED_PATTERNS:
            if pattern in feature:
                violations.append({"column": feature, "type": f"prohibited_pattern:{pattern}"})
    report = {
        "checked_predictor_count": len(config.features.predictors),
        "prohibited_columns": sorted(explicit),
        "direct_leakage_violations": [
            item for item in violations if item["type"] == "explicit_prohibited"
        ],
        "temporal_leakage_violations": [
            item for item in violations if item["type"].startswith("prohibited_pattern")
        ],
        "identifier_leakage_violations": [
            item for item in violations if item["column"] in config.identifiers
        ],
        "group_leakage_violations": [],
        "total_violations": len(violations),
        "valid": not violations,
    }
    return LeakageResult(valid=not violations, violations=violations, report=report)


def assert_no_leakage(config: FeatureConfig) -> LeakageResult:
    result = check_leakage(config)
    if not result.valid:
        raise ValueError(f"Feature leakage violations detected: {result.violations}")
    return result
