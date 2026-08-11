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
                },
                {
                    "title": "Evaluating AI Agents",
                    "url": "https://example.com/evaluation",
                    "content": "Agent evaluation should measure groundedness.",
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
            "publisher": "Tavily",
            "excerpt": ("AI agent reliability depends on robust evaluation."),
        },
        {
            "title": "Evaluating AI Agents",
            "url": "https://example.com/evaluation",
            "publisher": "Tavily",
            "excerpt": "Agent evaluation should measure groundedness.",
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


def test_tavily_provider_works_with_real_client_shape(
    monkeypatch,
) -> None:
    class FakeClient:
        def search(self, query: str) -> dict:
            return {
                "results": [
                    {
                        "title": "AI Agent Reliability",
                        "url": "https://example.com/reliability",
                        "content": "Reliability depends on strong evaluation.",
                    }
                ]
            }

    provider = TavilySearchProvider(client=FakeClient())

    results = provider.search("AI agent reliability")

    assert results == [
        {
            "title": "AI Agent Reliability",
            "url": "https://example.com/reliability",
            "publisher": "Tavily",
            "excerpt": "Reliability depends on strong evaluation.",
        }
    ]
