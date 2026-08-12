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


def test_extractor_returns_evidence_from_content() -> None:
    extractor = EvidenceExtractor()

    source = make_source()

    evidence = extractor.extract(
        source=source,
        content="AI agents can fail unpredictably during multi-step tasks.",
        relevance=0.91,
    )

    assert evidence == Evidence(
        source=source,
        excerpt="AI agents can fail unpredictably during multi-step tasks.",
        relevance=0.91,
    )


def test_extractor_trims_content() -> None:
    extractor = EvidenceExtractor()

    source = make_source()

    evidence = extractor.extract(
        source=source,
        content="  Reliability requires strong evaluation.  ",
        relevance=0.84,
    )

    assert evidence.excerpt == "Reliability requires strong evaluation."


def test_extractor_limits_excerpt_length() -> None:
    extractor = EvidenceExtractor()

    source = make_source()

    content = "A" * 100

    evidence = extractor.extract(
        source=source,
        content=content,
        relevance=0.73,
        max_length=25,
    )

    assert evidence.excerpt == "A" * 25
    assert len(evidence.excerpt) == 25


def test_extractor_rejects_empty_content() -> None:
    extractor = EvidenceExtractor()

    source = make_source()

    with pytest.raises(ValueError, match="content must not be empty"):
        extractor.extract(
            source=source,
            content="   ",
            relevance=0.8,
        )


def test_extractor_rejects_invalid_max_length() -> None:
    extractor = EvidenceExtractor()

    source = make_source()

    with pytest.raises(ValueError, match="max_length"):
        extractor.extract(
            source=source,
            content="Reliability requires evaluation.",
            relevance=0.8,
            max_length=0,
        )
