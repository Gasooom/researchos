from datetime import UTC, datetime

import pytest

from app.application.retrieval.selector import SourceSelector
from app.domain.research.models import Source


def make_source(url: str, title: str) -> Source:
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


def test_selector_limits_number_of_sources() -> None:
    selector = SourceSelector(max_sources=2)

    sources = [
        make_source("https://example.com/1", "Source 1"),
        make_source("https://example.com/2", "Source 2"),
        make_source("https://example.com/3", "Source 3"),
    ]

    result = selector.select(sources)

    assert len(result) == 2


def test_selector_preserves_order() -> None:
    selector = SourceSelector(max_sources=2)

    sources = [
        make_source("https://example.com/1", "Source 1"),
        make_source("https://example.com/2", "Source 2"),
        make_source("https://example.com/3", "Source 3"),
    ]

    result = selector.select(sources)

    assert [source.title for source in result] == [
        "Source 1",
        "Source 2",
    ]


def test_selector_handles_fewer_sources_than_limit() -> None:
    selector = SourceSelector(max_sources=5)

    sources = [
        make_source("https://example.com/1", "Source 1"),
    ]

    assert selector.select(sources) == sources


def test_selector_handles_empty_sources() -> None:
    selector = SourceSelector(max_sources=5)

    assert selector.select([]) == []


def test_selector_rejects_invalid_limit() -> None:
    with pytest.raises(ValueError, match="max_sources"):
        SourceSelector(max_sources=0)
