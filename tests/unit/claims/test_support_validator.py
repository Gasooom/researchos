from datetime import UTC, datetime

import pytest

from app.application.claims.support_validator import (
    ClaimSupportValidator,
)
from app.domain.research.models import (
    Claim,
    Evidence,
    Source,
)
from app.domain.research.verification import (
    ClaimVerificationStatus,
)


def make_source() -> Source:
    return Source(
        title="AI Reliability Research",
        url="https://example.com/reliability",
        publisher="Example Research",
        retrieved_at=datetime(
            2026,
            8,
            13,
            18,
            0,
            tzinfo=UTC,
        ),
    )


def make_claim(
    statement: str,
    excerpt: str,
    relevance: float,
) -> Claim:
    source = make_source()

    evidence = Evidence(
        source=source,
        excerpt=excerpt,
        relevance=relevance,
    )

    return Claim(
        statement=statement,
        evidence=[evidence],
    )


def test_validator_supports_claim_with_relevant_matching_evidence() -> None:
    validator = ClaimSupportValidator()

    claim = make_claim(
        statement=("Independent evaluation improves AI agent reliability."),
        excerpt=(
            "Independent evaluation improves AI agent reliability "
            "by identifying failures."
        ),
        relevance=0.92,
    )

    result = validator.verify(claim)

    assert result.status == ClaimVerificationStatus.SUPPORTED
    assert result.confidence > 0.8
    assert result.matched_evidence_count == 1
    assert result.best_overlap >= 0.6
    assert result.best_relevance == 0.92


def test_validator_marks_partially_matching_evidence_as_weak() -> None:
    validator = ClaimSupportValidator()

    claim = make_claim(
        statement=(
            "Independent evaluation significantly improves AI agent reliability."
        ),
        excerpt=("Independent evaluation can identify failures in AI agents."),
        relevance=0.75,
    )

    result = validator.verify(claim)

    assert result.status == ClaimVerificationStatus.WEAK
    assert result.best_relevance == 0.75


def test_validator_rejects_irrelevant_evidence() -> None:
    validator = ClaimSupportValidator()

    claim = make_claim(
        statement="Independent evaluation improves AI reliability.",
        excerpt="Database indexing improves query performance.",
        relevance=0.9,
    )

    result = validator.verify(claim)

    assert result.status == ClaimVerificationStatus.UNSUPPORTED
    assert result.matched_evidence_count == 0


def test_validator_is_supported_matches_verification_status() -> None:
    validator = ClaimSupportValidator()

    supported_claim = make_claim(
        statement="Evaluation improves reliability.",
        excerpt="Evaluation improves reliability.",
        relevance=0.95,
    )

    unsupported_claim = make_claim(
        statement="Evaluation improves reliability.",
        excerpt="Database indexing improves performance.",
        relevance=0.95,
    )

    assert validator.is_supported(supported_claim)
    assert not validator.is_supported(unsupported_claim)


def test_validator_rejects_invalid_thresholds() -> None:
    with pytest.raises(
        ValueError,
        match="minimum_relevance",
    ):
        ClaimSupportValidator(
            minimum_relevance=1.1,
        )

    with pytest.raises(
        ValueError,
        match="weak_overlap",
    ):
        ClaimSupportValidator(
            weak_overlap=1.1,
        )

    with pytest.raises(
        ValueError,
        match="supported_overlap",
    ):
        ClaimSupportValidator(
            supported_overlap=1.1,
        )

    with pytest.raises(
        ValueError,
        match="must not exceed",
    ):
        ClaimSupportValidator(
            supported_overlap=0.4,
            weak_overlap=0.6,
        )
