from app.core.config import Settings, get_settings


def test_settings_use_development_defaults(monkeypatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_env == "development"
    assert settings.log_level == "INFO"


def test_settings_use_environment_values(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_env == "testing"
    assert settings.log_level == "DEBUG"


def test_get_settings_returns_cached_instance(monkeypatch) -> None:
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second


def test_settings_tavily_key_defaults_to_none(monkeypatch) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    settings = Settings(_env_file=None)

    assert settings.tavily_api_key is None


def test_settings_accept_tavily_api_key(monkeypatch) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    settings = Settings(_env_file=None)

    assert settings.tavily_api_key == "test-key"
