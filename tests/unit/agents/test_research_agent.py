import pytest
from pydantic import ValidationError

from app.application.orchestration.research_agent import ResearchAgent
from app.domain.research.models import ResearchTask


class StubSearchProvider:
    """Deterministic search provider for research-agent tests."""

    def search(self, query: str) -> list[dict[str, str | float]]:
        return [
            {
                "title": "AI Agent Reliability",
                "url": "https://example.com/reliability",
                "publisher": "Example Research",
                "excerpt": "AI agent reliability depends on robust evaluation.",
                "relevance": 0.92,
            }
        ]


def test_research_agent_accepts_search_provider() -> None:
    agent = ResearchAgent(search_provider=StubSearchProvider())

    assert isinstance(agent, ResearchAgent)


def test_research_agent_returns_evidence_for_task() -> None:
    agent = ResearchAgent(search_provider=StubSearchProvider())

    task = ResearchTask(
        objective="Investigate AI agent reliability.",
        task_type="reliability",
        max_sources=5,
    )

    evidence = agent.research(task)

    assert len(evidence) == 1

    result = evidence[0]

    assert result.source.title == "AI Agent Reliability"
    assert str(result.source.url) == "https://example.com/reliability"
    assert result.source.publisher == "Example Research"
    assert result.source.retrieved_at.tzinfo is not None
    assert result.excerpt == ("AI agent reliability depends on robust evaluation.")
    assert result.relevance == 0.92


def test_research_agent_passes_task_objective_to_search_provider() -> None:
    class RecordingSearchProvider:
        def __init__(self) -> None:
            self.query = None

        def search(self, query: str) -> list[dict[str, str | float]]:
            self.query = query
            return []

    provider = RecordingSearchProvider()
    agent = ResearchAgent(search_provider=provider)

    task = ResearchTask(
        objective="Investigate AI agent reliability.",
        task_type="reliability",
        max_sources=5,
    )

    agent.research(task)

    assert provider.query == "Investigate AI agent reliability."


def test_research_agent_rejects_invalid_search_result() -> None:
    class InvalidSearchProvider:
        def search(self, query: str) -> list[dict[str, str | float]]:
            return [
                {
                    "title": "",
                    "url": "https://example.com/reliability",
                    "publisher": "Example Research",
                    "excerpt": "Invalid evidence.",
                    "relevance": 0.92,
                }
            ]

    agent = ResearchAgent(search_provider=InvalidSearchProvider())

    task = ResearchTask(
        objective="Investigate AI agent reliability.",
        task_type="reliability",
        max_sources=5,
    )

    with pytest.raises(ValidationError):
        agent.research(task)


def test_research_agent_respects_max_sources() -> None:
    class MultiResultSearchProvider:
        def search(self, query: str) -> list[dict[str, str | float]]:
            return [
                {
                    "title": f"Source {index}",
                    "url": f"https://example.com/{index}",
                    "publisher": "Example Research",
                    "excerpt": f"Research excerpt {index}.",
                    "relevance": 0.9 - (index * 0.1),
                }
                for index in range(5)
            ]

    agent = ResearchAgent(search_provider=MultiResultSearchProvider())

    task = ResearchTask(
        objective="Investigate AI agent reliability.",
        task_type="reliability",
        max_sources=2,
    )

    evidence = agent.research(task)

    assert len(evidence) == 2
    assert evidence[0].source.title == "Source 0"
    assert evidence[1].source.title == "Source 1"
    assert evidence[0].relevance == 0.9
    assert evidence[1].relevance == 0.8
