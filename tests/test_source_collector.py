from datetime import datetime

from app.core.models.research import Source
from app.core.services.source_collector import SourceCollector


class StubClock:
    """Deterministic clock for collector tests."""

    def now(self) -> datetime:
        return datetime.fromisoformat("2026-08-11T00:00:00+00:00")


class StubSearchProvider:
    """Deterministic search provider for collector tests."""

    def search(self, query: str) -> list[dict[str, str | float]]:
        return [
            {
                "title": "AI Agent Reliability",
                "url": "https://example.com/reliability",
                "publisher": "example.com",
                "excerpt": "Reliability requires robust evaluation.",
                "relevance": 0.92,
            },
            {
                "title": "Evaluating AI Agents",
                "url": "https://research.example.org/evaluation",
                "publisher": "research.example.org",
                "excerpt": "Evaluation should measure groundedness.",
                "relevance": 0.81,
            },
        ]


def test_source_collector_returns_sources() -> None:
    collector = SourceCollector(clock=StubClock())

    results = StubSearchProvider().search("AI agent reliability")

    sources = collector.collect(results)

    assert sources == [
        Source(
            title="AI Agent Reliability",
            url="https://example.com/reliability",
            publisher="example.com",
            retrieved_at=datetime.fromisoformat("2026-08-11T00:00:00+00:00"),
        ),
        Source(
            title="Evaluating AI Agents",
            url="https://research.example.org/evaluation",
            publisher="research.example.org",
            retrieved_at=datetime.fromisoformat("2026-08-11T00:00:00+00:00"),
        ),
    ]


def test_source_collector_preserves_result_order() -> None:
    collector = SourceCollector(clock=StubClock())

    results = StubSearchProvider().search("AI agent reliability")

    sources = collector.collect(results)

    assert [source.title for source in sources] == [
        "AI Agent Reliability",
        "Evaluating AI Agents",
    ]


def test_source_collector_handles_empty_results() -> None:
    collector = SourceCollector(clock=StubClock())

    assert collector.collect([]) == []
