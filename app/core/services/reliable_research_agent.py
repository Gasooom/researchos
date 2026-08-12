"""Reliable research execution services for ResearchOS."""

from collections.abc import Callable
from time import sleep

from app.core.models.research import Evidence, ResearchTask
from app.core.services.research_agent import ResearchAgent
from app.core.services.research_failure import (
    PermanentResearchFailure,
    TransientResearchFailure,
)


class ReliableResearchAgent:
    """Add bounded retry behavior around classified failures."""

    def __init__(
        self,
        agent: ResearchAgent,
        max_attempts: int = 3,
        retry_delay: float = 0.0,
        sleeper: Callable[[float], None] = sleep,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        if retry_delay < 0:
            raise ValueError("retry_delay must not be negative")

        self.agent = agent
        self.max_attempts = max_attempts
        self.retry_delay = retry_delay
        self.sleeper = sleeper

    def research(self, task: ResearchTask) -> list[Evidence]:
        """Retry transient failures and propagate permanent failures."""
        for attempt in range(self.max_attempts):
            try:
                return self.agent.research(task)
            except PermanentResearchFailure:
                raise
            except TransientResearchFailure:
                if attempt == self.max_attempts - 1:
                    raise

                self.sleeper(self.retry_delay)

        raise RuntimeError("research attempts exhausted unexpectedly")
