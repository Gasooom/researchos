from datetime import UTC, datetime

from app.application.claims.critic import ClaimCritic
from app.domain.research.models import Claim, Evidence, Source


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


def test_critic_returns_no_issues_for_well_supported_claim() -> None:
    critic = ClaimCritic()

    claim = make_claim(
        statement="Evaluation improves AI reliability.",
        excerpts=[
            "Evaluation improves AI reliability.",
        ],
    )

    assert critic.inspect(claim) == []
    assert not critic.has_critical_issue(claim)


def test_critic_flags_claim_evidence_mismatch() -> None:
    critic = ClaimCritic()

    claim = make_claim(
        statement="Evaluation improves AI reliability.",
        excerpts=[
            "Database indexing improves query performance.",
        ],
    )

    issues = critic.inspect(claim)

    assert "weak claim/evidence support" in issues
    assert critic.has_critical_issue(claim)


def test_critic_flags_weak_evidence() -> None:
    critic = ClaimCritic()

    claim = make_claim(
        statement="Evaluation improves AI reliability.",
        excerpts=[
            "Evaluation improves reliability.",
        ],
        relevance=0.63,
    )

    issues = critic.inspect(claim)

    assert "weak evidence" in issues
    assert critic.has_critical_issue(claim)


def test_critic_flags_conflicting_evidence() -> None:
    critic = ClaimCritic()

    claim = make_claim(
        statement="Evaluation improves AI reliability.",
        excerpts=[
            "Evaluation improves AI reliability.",
            "Evaluation does not improve AI reliability.",
        ],
    )

    issues = critic.inspect(claim)

    assert issues == ["conflicting evidence"]
    assert critic.has_critical_issue(claim)
