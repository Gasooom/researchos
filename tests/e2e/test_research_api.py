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
from app.infrastructure.telemetry.run_observer import RunObserver


class StubSearchProvider:
    """Deterministic search provider for end-to-end tests."""

    def search(self, query: str) -> list[dict[str, str | float]]:
        return [
            {
                "title": "ResearchOS E2E Source",
                "url": "https://example.com/researchos-e2e",
                "publisher": "example.com",
                "excerpt": ("Evidence-grounded systems benefit from evaluation."),
                "relevance": 0.95,
            }
        ]


class StubClock:
    """Deterministic clock for source collection."""

    def now(self) -> datetime:
        return datetime(
            2026,
            8,
            13,
            9,
            30,
            tzinfo=UTC,
        )


def build_e2e_client() -> tuple[
    TestClient,
    InMemoryResearchRunRepository,
]:
    """Build a real ResearchOS application with deterministic infrastructure."""
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
        run_observer=RunObserver(),
    )

    service = ResearchApplicationService(
        orchestrator=orchestrator,
    )

    app = create_app(
        service=service,
        run_repository=repository,
    )

    return TestClient(app), repository


def test_research_request_persists_and_can_be_retrieved() -> None:
    client, repository = build_e2e_client()

    response = client.post(
        "/research",
        json={
            "question": ("How do evidence-grounded systems improve reliability?"),
            "max_sources": 1,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert (
        body["result"]["question"]
        == "How do evidence-grounded systems improve reliability?"
    )

    assert len(body["result"]["claims"]) == 3
    assert len(body["result"]["sources"]) == 1

    persisted_runs = repository.list()

    assert len(persisted_runs) == 1

    persisted_run = persisted_runs[0]

    assert persisted_run.completed_at is not None
    assert persisted_run.outcome is not None
    assert persisted_run.observation is not None
    assert persisted_run.observation.completed_tasks == 3
    assert persisted_run.observation.failed_tasks == 0
    assert persisted_run.observation.total_tasks == 3
    assert persisted_run.observation.status.value == "success"

    run_response = client.get(
        f"/runs/{persisted_run.id}",
    )

    assert run_response.status_code == 200

    run_body = run_response.json()

    assert run_body["run"]["id"] == str(persisted_run.id)
    assert run_body["run"]["outcome"]["status"] == "success"
    assert run_body["run"]["outcome"]["completed_tasks"] == 3
    assert run_body["run"]["outcome"]["failed_tasks"] == 0
    assert run_body["run"]["observation"]["total_tasks"] == 3


def test_research_api_returns_validation_error_for_missing_question() -> None:
    client, _ = build_e2e_client()

    response = client.post(
        "/research",
        json={
            "max_sources": 1,
        },
    )

    assert response.status_code == 422
