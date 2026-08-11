from app.core.services.search_provider import SearchProvider


class StubSearchProvider(SearchProvider):
    def search(self, query: str) -> list[dict[str, str]]:
        return [
            {
                "title": "AI Agent Reliability",
                "url": "https://example.com/reliability",
                "publisher": "Example Research",
                "excerpt": "AI agent reliability depends on robust evaluation.",
            }
        ]


def test_search_provider_returns_structured_results() -> None:
    provider = StubSearchProvider()

    results = provider.search("AI agent reliability")

    assert results == [
        {
            "title": "AI Agent Reliability",
            "url": "https://example.com/reliability",
            "publisher": "Example Research",
            "excerpt": "AI agent reliability depends on robust evaluation.",
        }
    ]
