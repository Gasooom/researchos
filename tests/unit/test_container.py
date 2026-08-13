from pathlib import Path

from app.application.research_service import ResearchApplicationService
from app.bootstrap.container import create_research_service
from app.core.config import Settings


class StubSearchProvider:
    """Deterministic search provider for composition tests."""

    def search(self, query: str) -> list[dict[str, str | float]]:
        return [
            {
                "title": "Example Source",
                "url": "https://example.com",
                "publisher": "example.com",
                "excerpt": "Example evidence.",
                "relevance": 0.9,
            }
        ]


def test_create_research_service_builds_application_service(
    tmp_path: Path,
) -> None:
    settings = Settings(
        tavily_api_key=None,
        research_database_path=str(
            tmp_path / "researchos.db",
        ),
    )

    service = create_research_service(
        settings=settings,
        search_provider=StubSearchProvider(),
    )

    assert isinstance(service, ResearchApplicationService)
