"""Compatibility checks between model, feature, and preprocessing contracts."""

from __future__ import annotations

from typing import Any


def validate_feature_contract(
    *,
    feature_names: list[str],
    preprocessor_metadata: dict[str, Any],
    expected_count: int,
) -> None:
    output_names = preprocessor_metadata.get("output_feature_names")
    if output_names != feature_names:
        raise ValueError("Feature schema mismatch between candidate bundle and preprocessor.")
    if len(feature_names) != expected_count:
        raise ValueError("Feature-count mismatch.")


def validate_test_lock(manifest: dict[str, Any], recommendation: dict[str, Any]) -> None:
    if manifest.get("test_set_used_for_selection") is not False:
        raise ValueError("Training manifest shows test set was used for selection.")
    if recommendation.get("test_set_used_for_selection") is not False:
        raise ValueError("Recommendation shows test set was used for selection.")
    if manifest.get("test_set_evaluated_after_selection") is not True:
        raise ValueError("Training manifest must show test set was evaluated after selection.")
