"""Synthesis-specialized agent for ResearchOS."""

from app.application.agents.roles import AgentRole
from app.domain.research.analysis import AnalysisResult
from app.domain.research.models import Evidence, ResearchTask
from app.domain.research.synthesis import SynthesisResult


class SynthesisAgent:
    """Synthesize analyzed evidence into a research answer."""

    @property
    def role(self) -> AgentRole:
        """Return this agent's specialization."""
        return AgentRole.SYNTHESIS

    def execute(
        self,
        task: ResearchTask,
        evidence: list[Evidence],
        analysis: AnalysisResult,
    ) -> SynthesisResult:
        """Produce a synthesis from research analysis."""
        if not evidence:
            raise ValueError("evidence must not be empty")

        if not analysis.key_points:
            raise ValueError("analysis must contain key points")

        supporting_points = list(analysis.key_points)

        return SynthesisResult(
            answer=(
                f"Based on the available evidence, "
                f"the main findings for '{task.objective}' are: "
                f"{' '.join(supporting_points)}"
            ),
            supporting_points=supporting_points,
            confidence=analysis.confidence,
        )
