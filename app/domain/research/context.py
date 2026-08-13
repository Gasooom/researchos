"""Research execution context models for ResearchOS."""

from pydantic import BaseModel, Field

from app.domain.research.memory import ResearchMemoryItem
from app.domain.research.models import ResearchRequest


class ResearchContext(BaseModel):
    """Context available during one research execution."""

    request: ResearchRequest
    historical_memory: list[ResearchMemoryItem] = Field(
        default_factory=list,
    )
