"""Evidence extraction services for ResearchOS."""

from app.domain.research.models import Evidence, Source


class EvidenceExtractor:
    """Extract a bounded supporting excerpt from source content."""

    def extract(
        self,
        source: Source,
        content: str,
        relevance: float,
        max_length: int = 500,
    ) -> Evidence:
        """Create evidence using a bounded excerpt from source content."""
        content = content.strip()

        if not content:
            raise ValueError("content must not be empty")

        if max_length < 1:
            raise ValueError("max_length must be at least 1")

        excerpt = content[:max_length].strip()

        return Evidence(
            source=source,
            excerpt=excerpt,
            relevance=relevance,
        )
