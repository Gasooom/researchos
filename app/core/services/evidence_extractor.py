"""Evidence extraction services for ResearchOS."""

from app.core.models.research import Evidence, Source


class EvidenceExtractor:
    """Create validated evidence from a source and supporting excerpt."""

    def extract(
        self,
        source: Source,
        excerpt: str,
        relevance: float,
    ) -> Evidence:
        """Create validated evidence from extracted source content."""
        if not excerpt.strip():
            raise ValueError("excerpt must not be empty")

        return Evidence(
            source=source,
            excerpt=excerpt.strip(),
            relevance=relevance,
        )
