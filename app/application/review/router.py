"""Claim review routing services for ResearchOS."""

from app.application.claims.support_classifier import (
    ClaimSupportClassifier,
    SupportLevel,
)
from app.domain.research.models import Claim
from app.domain.research.review import ReviewStatus


class ClaimReviewRouter:
    """Route claims into automatic or human review states."""

    def __init__(
        self,
        classifier: ClaimSupportClassifier | None = None,
    ) -> None:
        self.classifier = classifier or ClaimSupportClassifier()

    def route(self, claim: Claim) -> ReviewStatus:
        """Return the appropriate review status for a claim."""
        support_level = self.classifier.classify(claim)

        if support_level == SupportLevel.SUPPORTED:
            return ReviewStatus.NOT_REQUIRED

        return ReviewStatus.PENDING
