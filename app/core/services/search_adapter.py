"""Search client adapters for ResearchOS."""

from typing import Protocol

from app.core.services.search_provider import SearchProvider


class SearchClient(Protocol):
    """Protocol for concrete search clients."""

    def search(self, query: str) -> list[dict[str, str]]:
        """Search an external service and return structured results."""
        ...


class SearchAdapter(SearchProvider):
    """Adapt a concrete search client to the ResearchOS search contract."""

    def __init__(self, client: SearchClient) -> None:
        self.client = client

    def search(self, query: str) -> list[dict[str, str]]:
        """Run the query through the configured search client."""
        return self.client.search(query)
