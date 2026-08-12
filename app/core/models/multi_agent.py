"""Multi-agent research result models for ResearchOS."""

from pydantic import BaseModel, Field

from app.core.models.analysis import AnalysisResult
from app.core.models.research import Evidence
from app.core.models.synthesis import SynthesisResult


class MultiAgentResearchResult(BaseModel):
    """Combined output from the specialized research agents."""

    evidence: list[Evidence] = Field(min_length=1)
    analysis: AnalysisResult
    synthesis: SynthesisResult
