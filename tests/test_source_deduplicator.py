from datetime import UTC, datetime

from app.core.models.research import Source
from app.core.services.source_deduplicator import SourceDeduplicator


def make_source(
    url: str,
    title: str,
) -> Source:
    return Source(
        title=title,
        url=url,
        publisher="example.com",
        retrieved_at=datetime(
            2026,
            8,
            11,
            0,
            0,
            tzinfo=UTC,
        ),
    )


def test_deduplicator_removes_duplicate_urls() -> None:
    deduplicator = SourceDeduplicator()

    sources = [
        make_source(
            "https://example.com/article",
            "First version",
        ),
        make_source(
            "https://example.com/article",
            "Duplicate version",
        ),
        make_source(
            "https://example.com/other",
            "Other source",
        ),
    ]

    result = deduplicator.deduplicate(sources)

    assert result == [
        sources[0],
        sources[2],
    ]


def test_deduplicator_preserves_first_occurrence() -> None:
    deduplicator = SourceDeduplicator()

    first = make_source(
        "https://example.com/article",
        "First",
    )
    second = make_source(
        "https://example.com/article",
        "Second",
    )

    result = deduplicator.deduplicate([first, second])

    assert result[0] is first


def test_deduplicator_handles_empty_input() -> None:
    deduplicator = SourceDeduplicator()

    assert deduplicator.deduplicate([]) == []
