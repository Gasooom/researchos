"""Human calibration models for ResearchOS."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CalibrationLabel(BaseModel):
    """Human assessment of one evaluated research result."""

    groundedness: float = Field(ge=0.0, le=1.0)
    completeness: float = Field(ge=0.0, le=1.0)
    uncertainty_handling: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)


class CalibrationRecord(BaseModel):
    """Comparison between an LLM judge and human evaluation."""

    id: UUID = Field(default_factory=uuid4)
    llm_groundedness: float = Field(ge=0.0, le=1.0)
    llm_completeness: float = Field(ge=0.0, le=1.0)
    llm_uncertainty_handling: float = Field(ge=0.0, le=1.0)
    llm_overall_score: float = Field(ge=0.0, le=1.0)
    human: CalibrationLabel
    created_at: datetime
