"""Source verification services for ResearchOS."""

from urllib.parse import urlparse

from app.domain.research.models import Source
from app.domain.research.verification import (
    SourceVerification,
    SourceVerificationStatus,
)


class SourceVerifier:
    """Verify source metadata without making external network calls."""

    def verify(self, source: Source) -> SourceVerification:
        """Verify the structural quality of a source."""
        reasons: list[str] = []

        parsed_url = urlparse(str(source.url))

        if parsed_url.scheme not in {"http", "https"}:
            reasons.append("source URL must use HTTP or HTTPS")

        if not parsed_url.netloc:
            reasons.append("source URL must contain a host")

        if not source.title.strip():
            reasons.append("source title must not be empty")

        if not source.publisher.strip():
            reasons.append("source publisher must not be empty")

        if reasons:
            return SourceVerification(
                status=SourceVerificationStatus.REJECTED,
                reasons=reasons,
            )

        return SourceVerification(
            status=SourceVerificationStatus.VERIFIED,
            reasons=["source metadata is structurally valid"],
        )
