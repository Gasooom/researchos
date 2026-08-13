"""Multi-agent research coordination services for ResearchOS."""

from typing import Protocol

from app.application.agents.roles import AgentRole
from app.domain.research.analysis import AnalysisResult
from app.domain.research.models import Evidence, ResearchTask
from app.domain.research.multi_agent import MultiAgentResearchResult
from app.domain.research.synthesis import SynthesisResult


class RetrievalAgentLike(Protocol):
    """Behavior required from a retrieval agent."""

    @property
    def role(self) -> AgentRole:
        """Return the agent role."""
        ...

    def execute(self, task: ResearchTask) -> list[Evidence]:
        """Retrieve evidence for a task."""
        ...


class AnalysisAgentLike(Protocol):
    """Behavior required from an analysis agent."""

    @property
    def role(self) -> AgentRole:
        """Return the agent role."""
        ...

    def execute(
        self,
        task: ResearchTask,
        evidence: list[Evidence],
    ) -> AnalysisResult:
        """Analyze evidence for a task."""
        ...


class SynthesisAgentLike(Protocol):
    """Behavior required from a synthesis agent."""

    @property
    def role(self) -> AgentRole:
        """Return the agent role."""
        ...

    def execute(
        self,
        task: ResearchTask,
        evidence: list[Evidence],
        analysis: AnalysisResult,
    ) -> SynthesisResult:
        """Synthesize a research answer."""
        ...


class MultiAgentCoordinator:
    """Coordinate retrieval, analysis, and synthesis agents."""

    def __init__(
        self,
        retrieval_agent: RetrievalAgentLike,
        analysis_agent: AnalysisAgentLike,
        synthesis_agent: SynthesisAgentLike,
    ) -> None:
        self.retrieval_agent = retrieval_agent
        self.analysis_agent = analysis_agent
        self.synthesis_agent = synthesis_agent

    def execute(self, task: ResearchTask) -> MultiAgentResearchResult:
        """Run the complete specialized-agent workflow."""
        evidence = self.retrieval_agent.execute(task)

        if not evidence:
            raise ValueError("retrieval agent returned no evidence")

        analysis = self.analysis_agent.execute(
            task=task,
            evidence=evidence,
        )

        synthesis = self.synthesis_agent.execute(
            task=task,
            evidence=evidence,
            analysis=analysis,
        )

        return MultiAgentResearchResult(
            evidence=evidence,
            analysis=analysis,
            synthesis=synthesis,
        )
