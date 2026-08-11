"""Tavily-backed search provider for ResearchOS."""

from typing import Protocol
from urllib.parse import urlparse

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

    def search(self, query: str) -> list[dict[str, str | float]]:
        """Search Tavily and normalize the returned results."""
        response = self.client.search(query)

        normalized_results: list[dict[str, str | float]] = []

        for result in response.get("results", []):
            parsed_url = urlparse(result["url"])
            publisher = parsed_url.netloc or "unknown"

            normalized_results.append(
                {
                    "title": result["title"],
                    "url": result["url"],
                    "publisher": publisher,
                    "excerpt": result["content"],
                    "relevance": float(result.get("score", 0.0)),
                }
            )

        return normalized_results


def create_tavily_search_provider(settings: Settings) -> TavilySearchProvider:
    """Create a Tavily search provider from application settings."""
    client = create_tavily_client(settings)

    return TavilySearchProvider(client=client)
