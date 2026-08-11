"""Research execution services for ResearchOS."""

from datetime import UTC, datetime

from app.core.models.research import Evidence, ResearchTask, Source
from app.core.services.search_provider import SearchProvider


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
                title=str(result["title"]),
                url=str(result["url"]),
                publisher=str(result["publisher"]),
                retrieved_at=retrieved_at,
            )

            evidence.append(
                Evidence(
                    source=source,
                    excerpt=str(result["excerpt"]),
                    relevance=float(result.get("relevance", 0.0)),
                )
            )

        return evidence
