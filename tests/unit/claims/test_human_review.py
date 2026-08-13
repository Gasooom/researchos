import pytest

from app.application.review.service import HumanReviewService
from app.domain.research.review import (
    ReviewDecision,
    ReviewStatus,
)


def test_human_review_approves_pending_review() -> None:
    service = HumanReviewService()

    result = service.apply(
        status=ReviewStatus.PENDING,
        decision=ReviewDecision.APPROVE,
    )

    assert result.status == ReviewStatus.APPROVED
    assert result.decision == ReviewDecision.APPROVE


def test_human_review_rejects_pending_review() -> None:
    service = HumanReviewService()

    result = service.apply(
        status=ReviewStatus.PENDING,
        decision=ReviewDecision.REJECT,
    )

    assert result.status == ReviewStatus.REJECTED
    assert result.decision == ReviewDecision.REJECT


def test_human_review_requests_more_evidence() -> None:
    service = HumanReviewService()

    result = service.apply(
        status=ReviewStatus.PENDING,
        decision=ReviewDecision.REQUEST_MORE_EVIDENCE,
    )

    assert result.status == ReviewStatus.PENDING
    assert result.decision == ReviewDecision.REQUEST_MORE_EVIDENCE


def test_human_review_requires_pending_status() -> None:
    service = HumanReviewService()

    with pytest.raises(
        ValueError,
        match="requires a pending review",
    ):
        service.apply(
            status=ReviewStatus.NOT_REQUIRED,
            decision=ReviewDecision.APPROVE,
        )
