"""Source deduplication services for ResearchOS."""

from app.domain.research.models import Source


class SourceDeduplicator:
    """Remove duplicate sources while preserving first occurrence order."""

    def deduplicate(self, sources: list[Source]) -> list[Source]:
        """Return unique sources based on their normalized URL."""
        seen_urls: set[str] = set()
        unique_sources: list[Source] = []

        for source in sources:
            normalized_url = str(source.url).rstrip("/")

            if normalized_url in seen_urls:
                continue

            seen_urls.add(normalized_url)
            unique_sources.append(source)

        return unique_sources
