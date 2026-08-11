"""Search provider contracts for ResearchOS."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class SearchProvider(Protocol):
    """Contract for services that return structured search results."""

    def search(self, query: str) -> list[dict[str, str]]:
        """Search for relevant sources using a query."""
        ...
