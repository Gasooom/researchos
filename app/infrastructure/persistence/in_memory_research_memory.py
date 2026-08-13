"""In-memory research memory repository for ResearchOS."""

from app.domain.research.memory import ResearchMemoryItem


class InMemoryResearchMemoryRepository:
    """Store research memory items in memory."""

    def __init__(self) -> None:
        self._items: list[ResearchMemoryItem] = []

    def save(
        self,
        item: ResearchMemoryItem,
    ) -> ResearchMemoryItem:
        """Persist a memory item."""
        self._items.append(item)
        return item

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[ResearchMemoryItem]:
        """Return memory items matching query terms."""
        if limit < 1:
            raise ValueError("limit must be at least 1")

        normalized_query = query.strip().lower()

        if not normalized_query:
            return []

        query_terms = set(normalized_query.split())

        scored_items: list[tuple[int, ResearchMemoryItem]] = []

        for item in self._items:
            text = (
                f"{item.question} "
                f"{item.summary} " + " ".join(claim.statement for claim in item.claims)
            ).lower()

            score = sum(term in text for term in query_terms)

            if score > 0:
                scored_items.append(
                    (score, item),
                )

        scored_items.sort(
            key=lambda pair: pair[0],
            reverse=True,
        )

        return [item for _, item in scored_items[:limit]]

    def list(self) -> list[ResearchMemoryItem]:
        """Return all stored memory items."""
        return list(self._items)
