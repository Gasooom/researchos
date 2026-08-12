"""Synthesis domain models for ResearchOS."""

from pydantic import BaseModel, Field


class SynthesisResult(BaseModel):
    """Structured synthesis produced from research analysis."""

    answer: str = Field(min_length=1)
    supporting_points: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
