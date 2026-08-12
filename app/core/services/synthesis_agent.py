"""Synthesis-specialized agent for ResearchOS."""

from app.core.models.analysis import AnalysisResult
from app.core.models.research import Evidence, ResearchTask
from app.core.models.synthesis import SynthesisResult
from app.core.services.agent_roles import AgentRole


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
