from datetime import UTC, datetime

import pytest

from app.core.models.research import Evidence, Source
from app.core.services.evidence_extractor import EvidenceExtractor


def make_source() -> Source:
    return Source(
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


def test_extractor_returns_evidence() -> None:
    extractor = EvidenceExtractor()

    source = make_source()

    evidence = extractor.extract(
        source=source,
        excerpt="AI agents can fail unpredictably during multi-step tasks.",
        relevance=0.91,
    )

    assert evidence == Evidence(
        source=source,
        excerpt="AI agents can fail unpredictably during multi-step tasks.",
        relevance=0.91,
    )


def test_extractor_preserves_source_metadata() -> None:
    extractor = EvidenceExtractor()

    source = make_source()

    evidence = extractor.extract(
        source=source,
        excerpt="Reliability requires strong evaluation.",
        relevance=0.84,
    )

    assert evidence.source == source


def test_extractor_preserves_relevance() -> None:
    extractor = EvidenceExtractor()

    source = make_source()

    evidence = extractor.extract(
        source=source,
        excerpt="Reliability requires strong evaluation.",
        relevance=0.73,
    )

    assert evidence.relevance == 0.73


def test_extractor_rejects_empty_excerpt() -> None:
    extractor = EvidenceExtractor()

    source = make_source()

    with pytest.raises(ValueError, match="excerpt must not be empty"):
        extractor.extract(
            source=source,
            excerpt="",
            relevance=0.8,
        )
