from app.core.services.search_provider import SearchProvider
from app.core.services.tavily_search_provider import TavilySearchProvider


class FakeTavilyClient:
    """Deterministic Tavily client for adapter tests."""

    def search(self, query: str) -> dict:
        return {
            "results": [
                {
                    "title": "AI Agent Reliability",
                    "url": "https://example.com/reliability",
                    "content": ("AI agent reliability depends on robust evaluation."),
                    "score": 0.92,
                },
                {
                    "title": "Evaluating AI Agents",
                    "url": "https://research.example.org/evaluation",
                    "content": "Agent evaluation should measure groundedness.",
                    "score": 0.81,
                },
            ]
        }


def test_tavily_provider_implements_search_provider() -> None:
    provider = TavilySearchProvider(client=FakeTavilyClient())

    assert isinstance(provider, SearchProvider)


def test_tavily_provider_normalizes_results() -> None:
    provider = TavilySearchProvider(client=FakeTavilyClient())

    results = provider.search("AI agent reliability")

    assert results == [
        {
            "title": "AI Agent Reliability",
            "url": "https://example.com/reliability",
            "publisher": "example.com",
            "excerpt": ("AI agent reliability depends on robust evaluation."),
            "relevance": 0.92,
        },
        {
            "title": "Evaluating AI Agents",
            "url": "https://research.example.org/evaluation",
            "publisher": "research.example.org",
            "excerpt": "Agent evaluation should measure groundedness.",
            "relevance": 0.81,
        },
    ]


def test_tavily_provider_passes_query_to_client() -> None:
    class RecordingTavilyClient:
        def __init__(self) -> None:
            self.query = None

        def search(self, query: str) -> dict:
            self.query = query
            return {"results": []}

    client = RecordingTavilyClient()
    provider = TavilySearchProvider(client=client)

    provider.search("AI agent reliability")

    assert client.query == "AI agent reliability"


def test_tavily_provider_handles_empty_results() -> None:
    class EmptyTavilyClient:
        def search(self, query: str) -> dict:
            return {"results": []}

    provider = TavilySearchProvider(client=EmptyTavilyClient())

    assert provider.search("AI agent reliability") == []


def test_tavily_provider_uses_zero_when_score_is_missing() -> None:
    class MissingScoreClient:
        def search(self, query: str) -> dict:
            return {
                "results": [
                    {
                        "title": "AI Agent Reliability",
                        "url": "https://example.com/reliability",
                        "content": "Reliability requires evaluation.",
                    }
                ]
            }

    provider = TavilySearchProvider(client=MissingScoreClient())

    results = provider.search("AI agent reliability")

    assert results[0]["relevance"] == 0.0
