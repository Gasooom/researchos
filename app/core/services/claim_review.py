"""Claim review routing services for ResearchOS."""

from app.core.models.research import Claim
from app.core.models.review import ReviewStatus
from app.core.services.claim_support_classifier import (
    ClaimSupportClassifier,
    SupportLevel,
)


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
