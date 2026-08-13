"""Repository contracts for research runs."""

from typing import Protocol
from uuid import UUID

from app.domain.runs.record import ResearchRunRecord


class ResearchRunRepository(Protocol):
    """Persistence contract for research run records."""

    def save(self, run: ResearchRunRecord) -> ResearchRunRecord:
        """Persist a research run and return the stored record."""
        ...

    def get(self, run_id: UUID) -> ResearchRunRecord | None:
        """Return a run by identifier, or None when it does not exist."""
        ...

    def list(self) -> list[ResearchRunRecord]:
        """Return all persisted research runs."""
        ...
