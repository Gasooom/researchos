"""Human review services for ResearchOS."""

from dataclasses import dataclass

from app.domain.research.review import (
    ReviewDecision,
    ReviewStatus,
)


@dataclass(frozen=True)
class ReviewResult:
    """Result of applying a human review decision."""

    status: ReviewStatus
    decision: ReviewDecision | None = None


class HumanReviewService:
    """Apply explicit human decisions to reviewable claims."""

    def apply(
        self,
        status: ReviewStatus,
        decision: ReviewDecision,
    ) -> ReviewResult:
        """Apply a human decision to a pending review."""
        if status != ReviewStatus.PENDING:
            raise ValueError("human review requires a pending review")

        if decision == ReviewDecision.APPROVE:
            return ReviewResult(
                status=ReviewStatus.APPROVED,
                decision=decision,
            )

        if decision == ReviewDecision.REJECT:
            return ReviewResult(
                status=ReviewStatus.REJECTED,
                decision=decision,
            )

        if decision == ReviewDecision.REQUEST_MORE_EVIDENCE:
            return ReviewResult(
                status=ReviewStatus.PENDING,
                decision=decision,
            )

        raise ValueError(f"unsupported review decision: {decision}")
