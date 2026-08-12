import pytest

from app.core.models.research import Evidence, Source
from app.core.services.claim_grounder import ClaimGrounder


def make_evidence(relevance: float = 0.9) -> Evidence:
    source = Source(
        title="AI Agent Reliability",
        url="https://example.com/reliability",
        publisher="example.com",
        retrieved_at="2026-08-12T07:00:00+00:00",
    )

    return Evidence(
        source=source,
        excerpt="AI agents can fail unpredictably during multi-step tasks.",
        relevance=relevance,
    )


def test_grounder_creates_claim_from_evidence() -> None:
    grounder = ClaimGrounder()

    evidence = [make_evidence()]

    claim = grounder.ground(
        statement="AI agents can fail unpredictably in multi-step tasks.",
        evidence=evidence,
    )

    assert claim.statement == ("AI agents can fail unpredictably in multi-step tasks.")
    assert claim.evidence == evidence


def test_grounder_preserves_all_evidence() -> None:
    grounder = ClaimGrounder()

    evidence = [
        make_evidence(0.9),
        make_evidence(0.8),
    ]

    claim = grounder.ground(
        statement="AI agent reliability remains challenging.",
        evidence=evidence,
    )

    assert claim.evidence == evidence
    assert len(claim.evidence) == 2


def test_grounder_rejects_empty_statement() -> None:
    grounder = ClaimGrounder()

    with pytest.raises(ValueError, match="statement"):
        grounder.ground(
            statement="   ",
            evidence=[make_evidence()],
        )


def test_grounder_rejects_missing_evidence() -> None:
    grounder = ClaimGrounder()

    with pytest.raises(ValueError, match="evidence"):
        grounder.ground(
            statement="AI agents can fail unpredictably.",
            evidence=[],
        )
