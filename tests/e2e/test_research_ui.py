from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.app import create_app
from app.application.claims.grounder import ClaimGrounder
from app.application.claims.support_classifier import (
    ClaimSupportClassifier,
)
from app.application.evidence.extractor import EvidenceExtractor
from app.application.orchestration.planning import DeterministicPlanner
from app.application.orchestration.reliable_agent import ReliableResearchAgent
from app.application.orchestration.research import ResearchOrchestrator
from app.application.orchestration.research_agent import ResearchAgent
from app.application.orchestration.run_executor import ResearchRunExecutor
from app.application.research_service import ResearchApplicationService
from app.application.retrieval.collector import SourceCollector
from app.application.retrieval.deduplicator import SourceDeduplicator
from app.application.retrieval.selector import SourceSelector
from app.application.review.router import ClaimReviewRouter
from app.infrastructure.persistence.in_memory_run_repository import (
    InMemoryResearchRunRepository,
)


class StubSearchProvider:
    """Deterministic search provider for UI tests."""

    def search(self, query: str) -> list[dict[str, str | float]]:
        return [
            {
                "title": "ResearchOS UI Source",
                "url": "https://example.com/ui",
                "publisher": "example.com",
                "excerpt": (
                    "Evidence-grounded research improves research reliability."
                ),
                "relevance": 0.95,
            }
        ]


class StubClock:
    """Deterministic clock for UI tests."""

    def now(self) -> datetime:
        return datetime(
            2026,
            8,
            13,
            20,
            0,
            tzinfo=UTC,
        )


def build_client() -> TestClient:
    """Build a deterministic ResearchOS client."""
    repository = InMemoryResearchRunRepository()

    research_agent = ResearchAgent(
        search_provider=StubSearchProvider(),
    )

    reliable_agent = ReliableResearchAgent(
        agent=research_agent,
    )

    orchestrator = ResearchOrchestrator(
        planner=DeterministicPlanner(),
        run_executor=ResearchRunExecutor(
            research_agent=reliable_agent,
        ),
        source_collector=SourceCollector(
            clock=StubClock(),
        ),
        source_deduplicator=SourceDeduplicator(),
        source_selector=SourceSelector(max_sources=3),
        evidence_extractor=EvidenceExtractor(),
        claim_grounder=ClaimGrounder(),
        claim_support_classifier=ClaimSupportClassifier(),
        claim_review_router=ClaimReviewRouter(),
        multi_agent_coordinator=None,
        run_repository=repository,
    )

    service = ResearchApplicationService(
        orchestrator=orchestrator,
    )

    app = create_app(
        service=service,
        run_repository=repository,
    )

    return TestClient(app)


def test_ui_home_page_renders() -> None:
    client = build_client()

    response = client.get("/ui/")

    assert response.status_code == 200
    assert "ResearchOS" in response.text
    assert "Research question" in response.text
    assert "Run Research" in response.text


def test_ui_research_form_renders_result() -> None:
    client = build_client()

    response = client.post(
        "/ui/research",
        data={
            "question": "How does evidence improve research reliability?",
        },
    )

    assert response.status_code == 200
    assert "How does evidence improve research reliability?" in response.text
    assert "ResearchOS UI Source" in response.text
    assert "Evidence-grounded research improves research reliability." in (
        response.text
    )
    assert "success" in response.text
