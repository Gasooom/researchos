"""Claim review routing services for ResearchOS."""

from app.application.claims.critic import ClaimCritic
from app.domain.research.models import Claim
from app.domain.research.review import ReviewStatus


class ClaimReviewRouter:
    """Route claims into automatic or human review states."""

    def __init__(
        self,
        critic: ClaimCritic | None = None,
    ) -> None:
        self.critic = critic or ClaimCritic()

    def route(self, claim: Claim) -> ReviewStatus:
        """Return the appropriate review status for a claim."""
        if self.critic.has_critical_issue(claim):
            return ReviewStatus.PENDING

        return ReviewStatus.NOT_REQUIRED
