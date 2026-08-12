"""Contracts for specialized research agents."""

from typing import Protocol

from app.application.agents.roles import AgentRole
from app.domain.research.models import Evidence, ResearchTask


class SpecializedResearchAgent(Protocol):
    """Contract implemented by specialized research agents."""

    @property
    def role(self) -> AgentRole:
        """Return the agent's specialization."""
        ...

    def execute(
        self,
        task: ResearchTask,
    ) -> list[Evidence]:
        """Execute the task within the agent's specialization."""
        ...
