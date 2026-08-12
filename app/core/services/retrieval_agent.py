"""Retrieval-specialized agent for ResearchOS."""

from datetime import UTC, datetime

from app.core.models.research import Evidence, ResearchTask, Source
from app.core.services.agent_roles import AgentRole
from app.core.services.research_agent_contract import SpecializedResearchAgent
from app.core.services.search_provider import SearchProvider


class RetrievalAgent(SpecializedResearchAgent):
    """Retrieve and normalize evidence for a research task."""

    def __init__(self, search_provider: SearchProvider) -> None:
        self.search_provider = search_provider

    @property
    def role(self) -> AgentRole:
        """Return this agent's specialization."""
        return AgentRole.RETRIEVAL

    def execute(self, task: ResearchTask) -> list[Evidence]:
        """Search for sources and convert them into evidence."""
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
                    relevance=float(result["relevance"]),
                )
            )

        return evidence
