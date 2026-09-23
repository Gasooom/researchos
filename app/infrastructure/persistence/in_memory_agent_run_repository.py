"""In-memory agent run repository for ResearchOS."""

from uuid import UUID

from app.domain.tracing.models import AgentRun


class InMemoryAgentRunRepository:
    """Store agent run traces in memory."""

    def __init__(self) -> None:
        self._runs: dict[UUID, AgentRun] = {}

    def save(self, run: AgentRun) -> AgentRun:
        """Persist or replace an agent run."""
        self._runs[run.id] = run
        return run

    def get(self, run_id: UUID) -> AgentRun | None:
        """Return a stored agent run by identifier."""
        return self._runs.get(run_id)

    def list(self) -> list[AgentRun]:
        """Return all stored agent runs in insertion order."""
        return list(self._runs.values())
