"""Claim support validation services for ResearchOS."""

from app.domain.research.models import Claim


class ClaimSupportValidator:
    """Validate whether a claim has sufficiently relevant evidence."""

    def __init__(self, minimum_relevance: float = 0.7) -> None:
        if not 0.0 <= minimum_relevance <= 1.0:
            raise ValueError("minimum_relevance must be between 0 and 1")

        self.minimum_relevance = minimum_relevance

    def is_supported(self, claim: Claim) -> bool:
        """Return whether at least one evidence item meets the threshold."""
        return any(
            evidence.relevance >= self.minimum_relevance for evidence in claim.evidence
        )
