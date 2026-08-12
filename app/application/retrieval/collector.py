"""Source collection services for ResearchOS."""

from datetime import datetime
from typing import Protocol

from app.domain.research.models import Source


class Clock(Protocol):
    """Protocol for obtaining the current timestamp."""

    def now(self) -> datetime:
        """Return the current timezone-aware timestamp."""
        ...


class SourceCollector:
    """Convert normalized search results into validated Source objects."""

    def __init__(self, clock: Clock) -> None:
        self.clock = clock

    def collect(
        self,
        results: list[dict[str, str | float]],
    ) -> list[Source]:
        """Convert search results into domain Source objects."""
        retrieved_at = self.clock.now()

        return [
            Source(
                title=str(result["title"]),
                url=str(result["url"]),
                publisher=str(result["publisher"]),
                retrieved_at=retrieved_at,
            )
            for result in results
        ]
