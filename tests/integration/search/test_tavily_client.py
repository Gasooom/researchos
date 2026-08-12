import pytest

from app.core.config import Settings
from app.infrastructure.search.tavily_client import create_tavily_client


def test_create_tavily_client_uses_configured_api_key(
    monkeypatch,
) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    settings = Settings(_env_file=None)

    client = create_tavily_client(settings)

    assert client is not None


def test_create_tavily_client_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    settings = Settings(_env_file=None)

    with pytest.raises(ValueError, match="TAVILY_API_KEY"):
        create_tavily_client(settings)
