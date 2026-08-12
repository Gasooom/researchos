"""Multi-agent research result models for ResearchOS."""

from pydantic import BaseModel, Field

from app.domain.research.analysis import AnalysisResult
from app.domain.research.models import Evidence
from app.domain.research.synthesis import SynthesisResult


class MultiAgentResearchResult(BaseModel):
    """Combined output from the specialized research agents."""

    evidence: list[Evidence] = Field(min_length=1)
    analysis: AnalysisResult
    synthesis: SynthesisResult
