"""HTTP schemas for ResearchOS."""

from pydantic import BaseModel, Field

from app.domain.research.models import ResearchResult
from app.domain.runs.record import ResearchRunRecord


class ResearchRequestSchema(BaseModel):
    """Request body for starting a research workflow."""

    question: str = Field(min_length=1)
    max_sources: int = Field(default=3, ge=1)


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str


class ResearchResponse(BaseModel):
    """HTTP representation of a research result."""

    result: ResearchResult


class RunResponse(BaseModel):
    """HTTP representation of a persisted run."""

    run: ResearchRunRecord
