"""Source selection services for ResearchOS."""

from app.domain.research.models import Source


class SourceSelector:
    """Select a bounded number of sources while preserving order."""

    def __init__(self, max_sources: int) -> None:
        if max_sources < 1:
            raise ValueError("max_sources must be at least 1")

        self.max_sources = max_sources

    def select(self, sources: list[Source]) -> list[Source]:
        """Return at most max_sources sources in their existing order."""
        return sources[: self.max_sources]
