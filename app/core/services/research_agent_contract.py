"""Contracts for specialized research agents."""

from typing import Protocol

from app.core.models.research import Evidence, ResearchTask
from app.core.services.agent_roles import AgentRole


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
