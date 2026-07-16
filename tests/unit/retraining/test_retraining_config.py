from pathlib import Path

import pytest

from ml_product.retraining import ComparisonConfig, RetrainingConfig


def test_retraining_config_disables_automatic_actions() -> None:
    config = RetrainingConfig.from_file(Path("config/retraining.yaml"))
    assert config.workflow.automatic_execution is False
    assert config.workflow.require_human_initiation is True
    assert config.controls.automatic_registration is False
    assert config.controls.automatic_approval is False
    assert config.controls.automatic_activation is False
    assert config.controls.automatic_deployment is False


def test_comparison_config_blocks_historical_test_selection() -> None:
    config = ComparisonConfig.from_file(Path("config/champion_challenger.yaml"))
    assert config.selection["use_historical_test_set_for_selection"] is False
    assert config.selection["prefer_champion_when_differences_are_small"] is True


def test_automatic_approval_enabled_fails() -> None:
    payload = RetrainingConfig.from_file(Path("config/retraining.yaml")).model_dump()
    payload["controls"]["automatic_approval"] = True
    with pytest.raises(ValueError, match="automatic"):
        RetrainingConfig.model_validate(payload)


def test_historical_test_selection_enabled_fails() -> None:
    payload = ComparisonConfig.from_file(Path("config/champion_challenger.yaml")).model_dump()
    payload["selection"]["use_historical_test_set_for_selection"] = True
    with pytest.raises(ValueError, match="Historical test"):
        ComparisonConfig.model_validate(payload)
