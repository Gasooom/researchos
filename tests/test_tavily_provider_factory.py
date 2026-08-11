from app.core.config import Settings
from app.core.services.tavily_search_provider import (
    TavilySearchProvider,
    create_tavily_search_provider,
)


def test_create_tavily_search_provider_uses_configured_client(
    monkeypatch,
) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    settings = Settings()

    provider = create_tavily_search_provider(settings)

    assert isinstance(provider, TavilySearchProvider)
