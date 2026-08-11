"""Research execution services for ResearchOS."""

from datetime import UTC, datetime
from typing import Protocol

from app.core.models.research import Evidence, ResearchTask, Source


class SearchProvider(Protocol):
    """Protocol for providers capable of searching for research evidence."""

    def search(self, query: str) -> list[dict[str, str]]:
        """Return structured search results for a query."""
        ...


class ResearchAgent:
    """Execute a research task using a configurable search provider."""

    def __init__(self, search_provider: SearchProvider) -> None:
        self.search_provider = search_provider

    def research(self, task: ResearchTask) -> list[Evidence]:
        """Execute a research task and convert results into validated evidence."""
        results = self.search_provider.search(task.objective)
        retrieved_at = datetime.now(UTC)

        evidence: list[Evidence] = []

        for result in results[: task.max_sources]:
            source = Source(
                title=result["title"],
                url=result["url"],
                publisher=result["publisher"],
                retrieved_at=retrieved_at,
            )

            evidence.append(
                Evidence(
                    source=source,
                    excerpt=result["excerpt"],
                    relevance=1.0,
                )
            )

        return evidence
