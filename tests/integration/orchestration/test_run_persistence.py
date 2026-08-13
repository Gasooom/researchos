from datetime import UTC, datetime

from app.application.claims.grounder import ClaimGrounder
from app.application.claims.support_classifier import (
    ClaimSupportClassifier,
)
from app.application.evidence.extractor import EvidenceExtractor
from app.application.orchestration.reliable_agent import ReliableResearchAgent
from app.application.orchestration.research import ResearchOrchestrator
from app.application.orchestration.research_agent import ResearchAgent
from app.application.orchestration.run_executor import ResearchRunExecutor
from app.application.retrieval.collector import SourceCollector
from app.application.retrieval.deduplicator import SourceDeduplicator
from app.application.retrieval.selector import SourceSelector
from app.application.review.router import ClaimReviewRouter
from app.domain.research.models import ResearchRequest, ResearchTask
from app.domain.runs.models import ResearchRunStatus
from app.infrastructure.persistence.in_memory_run_repository import (
    InMemoryResearchRunRepository,
)


class StubPlanner:
    """Deterministic planner for persistence integration tests."""

    def plan(self, request: ResearchRequest) -> list[ResearchTask]:
        return [
            ResearchTask(
                objective=request.question,
                task_type="research",
                max_sources=2,
            )
        ]


class StubSearchProvider:
    """Deterministic search provider for persistence integration tests."""

    def search(self, query: str) -> list[dict[str, str | float]]:
        return [
            {
                "title": "AI Reliability",
                "url": "https://example.com/reliability",
                "publisher": "example.com",
                "excerpt": "AI agents can fail unpredictably.",
                "relevance": 0.92,
            },
            {
                "title": "Agent Evaluation",
                "url": "https://example.org/evaluation",
                "publisher": "example.org",
                "excerpt": "Evaluation improves reliability.",
                "relevance": 0.81,
            },
        ]


class StubClock:
    """Deterministic clock for persistence integration tests."""

    def now(self) -> datetime:
        return datetime(
            2026,
            8,
            12,
            16,
            0,
            tzinfo=UTC,
        )


def build_orchestrator(
    repository: InMemoryResearchRunRepository,
) -> ResearchOrchestrator:
    """Build a deterministic orchestrator with run persistence."""
    research_agent = ResearchAgent(StubSearchProvider())
    reliable_agent = ReliableResearchAgent(research_agent)

    return ResearchOrchestrator(
        planner=StubPlanner(),
        run_executor=ResearchRunExecutor(reliable_agent),
        source_collector=SourceCollector(StubClock()),
        source_deduplicator=SourceDeduplicator(),
        source_selector=SourceSelector(max_sources=2),
        evidence_extractor=EvidenceExtractor(),
        claim_grounder=ClaimGrounder(),
        claim_support_classifier=ClaimSupportClassifier(),
        claim_review_router=ClaimReviewRouter(),
        run_repository=repository,
    )


def test_orchestrator_persists_completed_run() -> None:
    repository = InMemoryResearchRunRepository()
    orchestrator = build_orchestrator(repository)

    request = ResearchRequest(
        question="What are the main challenges of AI agent reliability?"
    )

    result = orchestrator.run(request)

    persisted_runs = repository.list()

    assert len(persisted_runs) == 1

    persisted_run = persisted_runs[0]

    assert persisted_run.completed_at is not None
    assert persisted_run.outcome == result.execution
    assert persisted_run.outcome.status == ResearchRunStatus.SUCCESS
    assert persisted_run.outcome.completed_tasks == 1
    assert persisted_run.outcome.failed_tasks == 0


def test_orchestrator_persists_without_changing_result() -> None:
    repository = InMemoryResearchRunRepository()
    orchestrator = build_orchestrator(repository)

    request = ResearchRequest(
        question="What are the main challenges of AI agent reliability?"
    )

    result = orchestrator.run(request)

    persisted_run = repository.list()[0]

    assert result.execution is not None
    assert persisted_run.outcome == result.execution
    assert result.question == request.question
    assert result.sources
    assert result.claims
