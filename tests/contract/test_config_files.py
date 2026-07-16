from pathlib import Path

import yaml

from scripts.validate_repository import REQUIRED_CONFIGS, VALID_INTEGRATION_MODES


def test_config_files_are_valid_yaml() -> None:
    for config in REQUIRED_CONFIGS:
        document = yaml.safe_load(Path(config).read_text(encoding="utf-8"))
        assert isinstance(document, dict), config


def test_config_files_have_required_metadata() -> None:
    for config in REQUIRED_CONFIGS:
        document = yaml.safe_load(Path(config).read_text(encoding="utf-8"))
        for key in ("version", "description", "implementation_status", "enabled"):
            assert key in document, f"{config} missing {key}"


def test_integration_modes_are_supported() -> None:
    settings = yaml.safe_load(Path("config/settings.yaml").read_text(encoding="utf-8"))

    assert set(settings["integration_modes"].values()).issubset(VALID_INTEGRATION_MODES)


def test_env_example_contains_no_obvious_credentials() -> None:
    text = Path(".env.example").read_text(encoding="utf-8").lower()

    assert "password=" not in text
    assert "secret=" not in text
    assert "token=" not in text
