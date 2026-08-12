from datetime import UTC, datetime

import pytest

from app.application.claims.support_validator import ClaimSupportValidator
from app.domain.research.models import Claim, Evidence, Source


def make_evidence(relevance: float) -> Evidence:
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

    return Evidence(
        source=source,
        excerpt="AI agents can fail unpredictably during multi-step tasks.",
        relevance=relevance,
    )


def make_claim(*relevances: float) -> Claim:
    evidence = [make_evidence(relevance) for relevance in relevances]

    return Claim(
        statement="AI agents can fail unpredictably during multi-step tasks.",
        evidence=evidence,
    )


def test_validator_accepts_claim_with_sufficient_evidence() -> None:
    validator = ClaimSupportValidator(minimum_relevance=0.7)

    claim = make_claim(0.92)

    assert validator.is_supported(claim) is True


def test_validator_rejects_claim_with_insufficient_evidence() -> None:
    validator = ClaimSupportValidator(minimum_relevance=0.7)

    claim = make_claim(0.42)

    assert validator.is_supported(claim) is False


def test_validator_accepts_claim_when_any_evidence_meets_threshold() -> None:
    validator = ClaimSupportValidator(minimum_relevance=0.7)

    claim = make_claim(0.41, 0.91, 0.38)

    assert validator.is_supported(claim) is True


def test_validator_rejects_invalid_threshold() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        ClaimSupportValidator(minimum_relevance=1.5)
