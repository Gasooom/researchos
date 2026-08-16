"""Tests for claim deduplication."""

from datetime import UTC, datetime

from app.application.claims.deduplicator import ClaimDeduplicator
from app.domain.research.models import (
    Claim,
    Evidence,
    Source,
)


def make_evidence(
    title: str,
    excerpt: str,
    relevance: float,
) -> Evidence:
    """Build deterministic evidence for tests."""
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
        excerpt=excerpt,
        relevance=relevance,
    )


def test_deduplicator_merges_near_duplicate_claims() -> None:
    deduplicator = ClaimDeduplicator()

    claims = [
        Claim(
            statement=("AI agents often fail because production data is incomplete."),
            evidence=[
                make_evidence(
                    "Source A",
                    "Production data is often incomplete.",
                    0.91,
                ),
            ],
        ),
        Claim(
            statement=("AI agents commonly fail when production data is incomplete."),
            evidence=[
                make_evidence(
                    "Source B",
                    ("Incomplete production data causes agent failures."),
                    0.88,
                ),
            ],
        ),
    ]

    result = deduplicator.deduplicate(
        claims,
    )

    assert len(result) == 1
    assert len(result[0].evidence) == 2
    assert result[0].evidence[0].relevance == 0.91


def test_deduplicator_preserves_distinct_claims() -> None:
    deduplicator = ClaimDeduplicator()

    claims = [
        Claim(
            statement=("Poor data quality causes agent failures."),
            evidence=[
                make_evidence(
                    "Data Source",
                    "Poor data causes failures.",
                    0.9,
                ),
            ],
        ),
        Claim(
            statement=("Tool misuse causes agent failures."),
            evidence=[
                make_evidence(
                    "Tool Source",
                    "Tool misuse causes failures.",
                    0.9,
                ),
            ],
        ),
    ]

    result = deduplicator.deduplicate(
        claims,
    )

    assert len(result) == 2


def test_deduplicator_handles_empty_input() -> None:
    deduplicator = ClaimDeduplicator()

    assert deduplicator.deduplicate([]) == []
