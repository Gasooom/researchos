"""Claim support classification services for ResearchOS."""

from enum import StrEnum

from app.domain.research.models import Claim


class SupportLevel(StrEnum):
    """Classification levels for claim support."""

    SUPPORTED = "supported"
    WEAK = "weak"
    UNSUPPORTED = "unsupported"


class ClaimSupportClassifier:
    """Classify claims based on their strongest supporting evidence."""

    def __init__(
        self,
        supported_threshold: float = 0.8,
        weak_threshold: float = 0.5,
    ) -> None:
        if not 0.0 <= weak_threshold <= 1.0:
            raise ValueError("weak_threshold must be between 0 and 1")

        if not 0.0 <= supported_threshold <= 1.0:
            raise ValueError("supported_threshold must be between 0 and 1")

        if weak_threshold > supported_threshold:
            raise ValueError("weak_threshold must not exceed supported_threshold")

        self.supported_threshold = supported_threshold
        self.weak_threshold = weak_threshold

    def classify(self, claim: Claim) -> SupportLevel:
        """Classify a claim using its strongest evidence relevance."""
        strongest_relevance = max(evidence.relevance for evidence in claim.evidence)

        if strongest_relevance >= self.supported_threshold:
            return SupportLevel.SUPPORTED

        if strongest_relevance >= self.weak_threshold:
            return SupportLevel.WEAK

        return SupportLevel.UNSUPPORTED
