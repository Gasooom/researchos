from datetime import UTC, datetime

from app.application.review.router import ClaimReviewRouter
from app.domain.research.models import Claim, Evidence, Source
from app.domain.research.review import ReviewStatus


def make_claim(relevance: float) -> Claim:
    source = Source(
        title="AI Agent Reliability",
        url="https://example.com/reliability",
        publisher="example.com",
        retrieved_at=datetime(
            2026,
            8,
            12,
            7,
            0,
            tzinfo=UTC,
        ),
    )

    evidence = Evidence(
        source=source,
        excerpt="AI agents can fail unpredictably.",
        relevance=relevance,
    )

    return Claim(
        statement="AI agents can fail unpredictably.",
        evidence=[evidence],
    )


def test_supported_claim_does_not_require_review() -> None:
    router = ClaimReviewRouter()

    assert router.route(make_claim(0.92)) == ReviewStatus.NOT_REQUIRED


def test_weak_claim_requires_review() -> None:
    router = ClaimReviewRouter()

    assert router.route(make_claim(0.63)) == ReviewStatus.PENDING


def test_unsupported_claim_requires_review() -> None:
    router = ClaimReviewRouter()

    assert router.route(make_claim(0.31)) == ReviewStatus.PENDING
