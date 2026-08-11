import pytest

from app.core.config import Settings
from app.core.services.tavily_client import create_tavily_client


def test_create_tavily_client_uses_configured_api_key(
    monkeypatch,
) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    settings = Settings()

    client = create_tavily_client(settings)

    assert client is not None


def test_create_tavily_client_requires_api_key() -> None:
    settings = Settings()

    with pytest.raises(ValueError, match="TAVILY_API_KEY"):
        create_tavily_client(settings)
