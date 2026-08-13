from datetime import UTC, datetime

from app.application.review.router import ClaimReviewRouter
from app.application.review.service import HumanReviewService
from app.domain.research.models import Claim, Evidence, Source
from app.domain.research.review import ReviewDecision, ReviewStatus


def make_claim(
    statement: str,
    excerpts: list[str],
    relevance: float = 0.95,
) -> Claim:
    source = Source(
        title="AI Reliability Research",
        url="https://example.com/reliability",
        publisher="example.com",
        retrieved_at=datetime(
            2026,
            8,
            13,
            20,
            0,
            tzinfo=UTC,
        ),
    )

    evidence = [
        Evidence(
            source=source,
            excerpt=excerpt,
            relevance=relevance,
        )
        for excerpt in excerpts
    ]

    return Claim(
        statement=statement,
        evidence=evidence,
    )


def test_clean_claim_bypasses_human_review() -> None:
    router = ClaimReviewRouter()

    claim = make_claim(
        statement="Evaluation improves AI reliability.",
        excerpts=[
            "Evaluation improves AI reliability.",
        ],
    )

    assert router.route(claim) == ReviewStatus.NOT_REQUIRED


def test_weak_claim_enters_human_review() -> None:
    router = ClaimReviewRouter()

    claim = make_claim(
        statement="Evaluation improves AI reliability.",
        excerpts=[
            "Evaluation improves reliability.",
        ],
        relevance=0.63,
    )

    assert router.route(claim) == ReviewStatus.PENDING


def test_conflicting_claim_enters_human_review() -> None:
    router = ClaimReviewRouter()

    claim = make_claim(
        statement="Evaluation improves AI reliability.",
        excerpts=[
            "Evaluation improves AI reliability.",
            "Evaluation does not improve AI reliability.",
        ],
    )

    assert router.route(claim) == ReviewStatus.PENDING


def test_pending_claim_can_be_approved_by_human() -> None:
    router = ClaimReviewRouter()
    review_service = HumanReviewService()

    claim = make_claim(
        statement="Evaluation improves AI reliability.",
        excerpts=[
            "Evaluation improves AI reliability.",
            "Evaluation does not improve AI reliability.",
        ],
    )

    status = router.route(claim)

    assert status == ReviewStatus.PENDING

    result = review_service.apply(
        status=status,
        decision=ReviewDecision.APPROVE,
    )

    assert result.status == ReviewStatus.APPROVED


def test_pending_claim_can_be_rejected_by_human() -> None:
    router = ClaimReviewRouter()
    review_service = HumanReviewService()

    claim = make_claim(
        statement="Evaluation improves AI reliability.",
        excerpts=[
            "Database indexing improves query performance.",
        ],
    )

    status = router.route(claim)

    assert status == ReviewStatus.PENDING

    result = review_service.apply(
        status=status,
        decision=ReviewDecision.REJECT,
    )

    assert result.status == ReviewStatus.REJECTED


def test_pending_claim_can_request_more_evidence() -> None:
    router = ClaimReviewRouter()
    review_service = HumanReviewService()

    claim = make_claim(
        statement="Evaluation improves AI reliability.",
        excerpts=[
            "Database indexing improves query performance.",
        ],
    )

    status = router.route(claim)

    assert status == ReviewStatus.PENDING

    result = review_service.apply(
        status=status,
        decision=ReviewDecision.REQUEST_MORE_EVIDENCE,
    )

    assert result.status == ReviewStatus.PENDING
