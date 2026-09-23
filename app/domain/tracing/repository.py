"""Repository contract for captured agent runs."""

from typing import Protocol
from uuid import UUID

from app.domain.tracing.models import AgentRun


class AgentRunRepository(Protocol):
    """Persistence contract for agent run traces."""

    def save(self, run: AgentRun) -> AgentRun:
        """Persist an agent run and return the stored record."""
        ...

    def get(self, run_id: UUID) -> AgentRun | None:
        """Return an agent run by identifier, or None when it does not exist."""
        ...

    def list(self) -> list[AgentRun]:
        """Return all persisted agent runs."""
        ...
