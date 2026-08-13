from datetime import UTC, datetime

from app.application.retrieval.verifier import SourceVerifier
from app.domain.research.models import Source
from app.domain.research.verification import (
    SourceVerification,
    SourceVerificationStatus,
)


def make_source() -> Source:
    return Source(
        title="Example Research",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at=datetime(
            2026,
            8,
            13,
            11,
            0,
            tzinfo=UTC,
        ),
    )


def test_source_verifier_accepts_valid_source() -> None:
    verifier = SourceVerifier()

    result = verifier.verify(make_source())

    assert isinstance(result, SourceVerification)
    assert result.status == SourceVerificationStatus.VERIFIED
    assert result.reasons == ["source metadata is structurally valid"]


def test_source_verifier_rejects_missing_title() -> None:
    verifier = SourceVerifier()

    source = make_source()
    source.title = " "

    result = verifier.verify(source)

    assert result.status == SourceVerificationStatus.REJECTED
    assert "source title must not be empty" in result.reasons


def test_source_verifier_rejects_missing_publisher() -> None:
    verifier = SourceVerifier()

    source = make_source()
    source.publisher = " "

    result = verifier.verify(source)

    assert result.status == SourceVerificationStatus.REJECTED
    assert "source publisher must not be empty" in result.reasons


def test_source_verifier_returns_all_rejection_reasons() -> None:
    verifier = SourceVerifier()

    source = make_source()
    source.title = " "
    source.publisher = " "

    result = verifier.verify(source)

    assert result.status == SourceVerificationStatus.REJECTED
    assert result.reasons == [
        "source title must not be empty",
        "source publisher must not be empty",
    ]


def test_verified_source_always_contains_reason() -> None:
    verifier = SourceVerifier()

    result = verifier.verify(make_source())

    assert result.status == SourceVerificationStatus.VERIFIED
    assert result.reasons
