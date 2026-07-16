from pathlib import Path

from pytest import MonkeyPatch

from ml_product.settings import config_path, load_config_document, load_settings


def test_settings_load_defaults() -> None:
    settings = load_settings()

    assert settings.app_env == "development"
    assert settings.denodo_integration_mode == "denodo_compatible_local"
    assert settings.sas_viya_integration_mode == "local_model_lifecycle"


def test_environment_override(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("MODEL_API_PORT", "9000")

    settings = load_settings()

    assert settings.app_env == "staging"
    assert settings.model_api_port == 9000


def test_config_document_loads() -> None:
    document = load_config_document(config_path("settings.yaml"))

    assert document.version == "0.1.0"
    assert document.enabled is True


def test_config_path_resolves_to_config_directory() -> None:
    assert config_path("settings.yaml") == Path.cwd() / "config" / "settings.yaml"
