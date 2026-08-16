"""Tests for claim ranking."""

from datetime import UTC, datetime

from app.application.claims.ranker import ClaimRanker
from app.domain.research.models import Claim, Evidence, Source


def make_evidence(
    title: str,
    relevance: float,
) -> Evidence:
    """Build deterministic evidence for ranking tests."""
    return Evidence(
        source=Source(
            title=title,
            url=(f"https://example.com/{title.lower().replace(' ', '-')}"),
            publisher="example.com",
            retrieved_at=datetime(
                2026,
                8,
                16,
                tzinfo=UTC,
            ),
        ),
        excerpt=f"Evidence from {title}.",
        relevance=relevance,
    )


def test_ranker_prefers_stronger_evidence() -> None:
    ranker = ClaimRanker(max_claims=2)

    weak = Claim(
        statement="Weak claim.",
        evidence=[
            make_evidence(
                "Source A",
                0.60,
            ),
        ],
    )

    strong = Claim(
        statement="Strong claim.",
        evidence=[
            make_evidence(
                "Source B",
                0.95,
            ),
        ],
    )

    result = ranker.rank(
        [weak, strong],
    )

    assert result[0].statement == "Strong claim."


def test_ranker_rewards_independent_sources() -> None:
    ranker = ClaimRanker(max_claims=2)

    single_source = Claim(
        statement="Single source claim.",
        evidence=[
            make_evidence(
                "Source A",
                0.90,
            ),
        ],
    )

    corroborated = Claim(
        statement="Corroborated claim.",
        evidence=[
            make_evidence(
                "Source B",
                0.90,
            ),
            make_evidence(
                "Source C",
                0.90,
            ),
        ],
    )

    result = ranker.rank(
        [single_source, corroborated],
    )

    assert result[0].statement == "Corroborated claim."


def test_ranker_limits_results() -> None:
    ranker = ClaimRanker(max_claims=2)

    claims = [
        Claim(
            statement=f"Claim {index}.",
            evidence=[
                make_evidence(
                    f"Source {index}",
                    0.90,
                ),
            ],
        )
        for index in range(5)
    ]

    result = ranker.rank(claims)

    assert len(result) == 2
