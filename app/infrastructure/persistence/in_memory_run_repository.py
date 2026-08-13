"""In-memory research run repository for ResearchOS."""

from uuid import UUID

from app.domain.runs.record import ResearchRunRecord


class InMemoryResearchRunRepository:
    """Store research run records in memory."""

    def __init__(self) -> None:
        self._runs: dict[UUID, ResearchRunRecord] = {}

    def save(self, run: ResearchRunRecord) -> ResearchRunRecord:
        """Persist or replace a research run."""
        self._runs[run.id] = run
        return run

    def get(self, run_id: UUID) -> ResearchRunRecord | None:
        """Return a stored run by identifier."""
        return self._runs.get(run_id)

    def list(self) -> list[ResearchRunRecord]:
        """Return all stored runs in insertion order."""
        return list(self._runs.values())
