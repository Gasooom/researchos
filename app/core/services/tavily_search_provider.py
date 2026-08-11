"""Tavily-backed search provider for ResearchOS."""

from typing import Protocol

from app.core.config import Settings
from app.core.services.search_provider import SearchProvider
from app.core.services.tavily_client import create_tavily_client


class TavilyClient(Protocol):
    """Protocol for the Tavily client used by the search provider."""

    def search(self, query: str) -> dict:
        """Run a search query and return the provider response."""
        ...


class TavilySearchProvider(SearchProvider):
    """Normalize Tavily search responses into ResearchOS search results."""

    def __init__(self, client: TavilyClient) -> None:
        self.client = client

    def search(self, query: str) -> list[dict[str, str]]:
        """Search Tavily and normalize the returned results."""
        response = self.client.search(query)

        return [
            {
                "title": result["title"],
                "url": result["url"],
                "publisher": "Tavily",
                "excerpt": result["content"],
            }
            for result in response.get("results", [])
        ]


def create_tavily_search_provider(settings: Settings) -> TavilySearchProvider:
    """Create a Tavily search provider from application settings."""
    client = create_tavily_client(settings)

    return TavilySearchProvider(client=client)
