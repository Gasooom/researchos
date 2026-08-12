"""Analysis-specialized agent for ResearchOS."""

from app.application.agents.roles import AgentRole
from app.domain.research.analysis import AnalysisResult
from app.domain.research.models import Evidence, ResearchTask


class AnalysisAgent:
    """Analyze retrieved evidence without performing retrieval."""

    @property
    def role(self) -> AgentRole:
        """Return this agent's specialization."""
        return AgentRole.ANALYSIS

    def execute(
        self,
        task: ResearchTask,
        evidence: list[Evidence],
    ) -> AnalysisResult:
        """Analyze evidence relevant to the research task."""
        if not evidence:
            raise ValueError("evidence must not be empty")

        key_points = [item.excerpt for item in evidence if item.excerpt.strip()]

        strongest_relevance = max(item.relevance for item in evidence)

        return AnalysisResult(
            summary=(
                f"Analysis of {len(evidence)} evidence items for: {task.objective}"
            ),
            key_points=key_points,
            confidence=strongest_relevance,
        )
