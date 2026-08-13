from datetime import UTC, datetime

from app.application.review.router import ClaimReviewRouter
from app.domain.research.models import Claim, Evidence, Source
from app.domain.research.review import ReviewStatus


def make_claim(
    relevance: float,
    statement: str = "AI agents can fail unpredictably.",
    excerpts: list[str] | None = None,
) -> Claim:
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

    evidence_texts = excerpts or ["AI agents can fail unpredictably."]

    evidence = [
        Evidence(
            source=source,
            excerpt=excerpt,
            relevance=relevance,
        )
        for excerpt in evidence_texts
    ]

    return Claim(
        statement=statement,
        evidence=evidence,
    )


def test_supported_claim_does_not_require_review() -> None:
    router = ClaimReviewRouter()

    assert (
        router.route(
            make_claim(0.92),
        )
        == ReviewStatus.NOT_REQUIRED
    )


def test_supported_claim_requires_review_when_evidence_does_not_match() -> None:
    router = ClaimReviewRouter()

    claim = make_claim(
        relevance=0.92,
        statement="AI agents can fail unpredictably.",
        excerpts=[
            "Database indexing improves query performance.",
        ],
    )

    assert router.route(claim) == ReviewStatus.PENDING


def test_conflicting_evidence_requires_review() -> None:
    router = ClaimReviewRouter()

    claim = make_claim(
        relevance=0.95,
        statement="Evaluation improves AI reliability.",
        excerpts=[
            "Evaluation improves AI reliability.",
            "Evaluation does not improve AI reliability.",
        ],
    )

    assert router.route(claim) == ReviewStatus.PENDING


def test_non_conflicting_multiple_evidence_items_can_pass() -> None:
    router = ClaimReviewRouter()

    claim = make_claim(
        relevance=0.95,
        statement="Evaluation improves AI reliability.",
        excerpts=[
            "Evaluation improves AI reliability.",
            "Evaluation helps identify AI reliability failures.",
        ],
    )

    assert router.route(claim) == ReviewStatus.NOT_REQUIRED


def test_weak_claim_requires_review() -> None:
    router = ClaimReviewRouter()

    assert (
        router.route(
            make_claim(0.63),
        )
        == ReviewStatus.PENDING
    )


def test_unsupported_claim_requires_review() -> None:
    router = ClaimReviewRouter()

    assert (
        router.route(
            make_claim(0.31),
        )
        == ReviewStatus.PENDING
    )
