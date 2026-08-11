from app.core.config import Settings, get_settings


def test_settings_use_development_defaults(monkeypatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    settings = Settings()

    assert settings.app_env == "development"
    assert settings.log_level == "INFO"


def test_settings_read_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings()

    assert settings.app_env == "testing"
    assert settings.log_level == "DEBUG"


def test_get_settings_returns_cached_instance(monkeypatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second
