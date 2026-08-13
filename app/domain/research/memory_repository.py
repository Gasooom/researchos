"""Research memory repository contract for ResearchOS."""

from typing import Protocol

from app.domain.research.memory import ResearchMemoryItem


class ResearchMemoryRepository(Protocol):
    """Store and retrieve reusable research memory."""

    def save(
        self,
        item: ResearchMemoryItem,
    ) -> ResearchMemoryItem:
        """Persist a memory item."""
        ...

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[ResearchMemoryItem]:
        """Retrieve memory items relevant to a query."""
        ...
