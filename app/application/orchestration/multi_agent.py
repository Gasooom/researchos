"""Multi-agent research coordination services for ResearchOS."""

from app.application.agents.analysis import AnalysisAgent
from app.application.agents.retrieval import RetrievalAgent
from app.application.agents.synthesis import SynthesisAgent
from app.domain.research.models import ResearchTask
from app.domain.research.multi_agent import MultiAgentResearchResult


class MultiAgentCoordinator:
    """Coordinate retrieval, analysis, and synthesis agents."""

    def __init__(
        self,
        retrieval_agent: RetrievalAgent,
        analysis_agent: AnalysisAgent,
        synthesis_agent: SynthesisAgent,
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
