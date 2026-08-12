from app.infrastructure.search.adapter import SearchAdapter
from app.infrastructure.search.provider import SearchProvider


class FakeSearchClient:
    """Deterministic search client for adapter tests."""

    def search(self, query: str) -> list[dict[str, str]]:
        return [
            {
                "title": "AI Agent Reliability",
                "url": "https://example.com/reliability",
                "publisher": "Example Research",
                "excerpt": "AI agent reliability depends on robust evaluation.",
            }
        ]


def test_search_adapter_returns_provider_results() -> None:
    adapter = SearchAdapter(client=FakeSearchClient())

    results = adapter.search("AI agent reliability")

    assert results == [
        {
            "title": "AI Agent Reliability",
            "url": "https://example.com/reliability",
            "publisher": "Example Research",
            "excerpt": "AI agent reliability depends on robust evaluation.",
        }
    ]


def test_search_adapter_passes_query_to_client() -> None:
    class RecordingSearchClient:
        def __init__(self) -> None:
            self.query = None

        def search(self, query: str) -> list[dict[str, str]]:
            self.query = query
            return []

    client = RecordingSearchClient()
    adapter = SearchAdapter(client=client)

    adapter.search("AI agent reliability")

    assert client.query == "AI agent reliability"


def test_search_adapter_implements_search_provider() -> None:
    adapter = SearchAdapter(client=FakeSearchClient())

    assert isinstance(adapter, SearchProvider)
