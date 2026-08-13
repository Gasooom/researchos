"""Research memory domain models for ResearchOS."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.research.models import Claim, Evidence


class ResearchMemoryItem(BaseModel):
    """Reusable research knowledge captured from a completed run."""

    id: UUID = Field(default_factory=uuid4)
    question: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    claims: list[Claim] = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)
    created_at: datetime
