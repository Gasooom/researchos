"""Persistent research run records for ResearchOS."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.domain.runs.models import ResearchRunOutcome
from app.domain.runs.observability import RunObservation


class ResearchRunRecord(BaseModel):
    """Persistable representation of one research execution."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime
    completed_at: datetime | None = None
    outcome: ResearchRunOutcome
    observation: RunObservation | None = None
