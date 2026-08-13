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
from app.infrastructure.persistence.in_memory_run_repository import (
    InMemoryResearchRunRepository,
)
from app.infrastructure.telemetry.run_observer import RunObserver


class StubPlanner:
    """Deterministic planner for observability integration tests."""

    def plan(self, request: ResearchRequest) -> list[ResearchTask]:
        return [
            ResearchTask(
                objective=request.question,
                task_type="research",
                max_sources=1,
            )
        ]


class StubSearchProvider:
    """Deterministic search provider for observability tests."""

    def search(self, query: str) -> list[dict[str, str | float]]:
        return [
            {
                "title": "Observability Source",
                "url": "https://example.com/observability",
                "publisher": "example.com",
                "excerpt": "Operational telemetry improves reliability.",
                "relevance": 0.9,
            }
        ]


class StubClock:
    """Deterministic clock for source timestamps."""

    def now(self) -> datetime:
        return datetime(
            2026,
            8,
            13,
            9,
            0,
            tzinfo=UTC,
        )


class StubObserver(RunObserver):
    """Deterministic run observer for integration tests."""

    def __init__(self) -> None:
        self.observed_duration: float | None = None

    def observe(self, outcome, duration_seconds):
        self.observed_duration = duration_seconds

        return super().observe(
            outcome=outcome,
            duration_seconds=duration_seconds,
        )


def build_orchestrator(
    repository: InMemoryResearchRunRepository,
    observer: StubObserver,
) -> ResearchOrchestrator:
    research_agent = ResearchAgent(StubSearchProvider())
    reliable_agent = ReliableResearchAgent(research_agent)

    return ResearchOrchestrator(
        planner=StubPlanner(),
        run_executor=ResearchRunExecutor(reliable_agent),
        source_collector=SourceCollector(StubClock()),
        source_deduplicator=SourceDeduplicator(),
        source_selector=SourceSelector(max_sources=1),
        evidence_extractor=EvidenceExtractor(),
        claim_grounder=ClaimGrounder(),
        claim_support_classifier=ClaimSupportClassifier(),
        claim_review_router=ClaimReviewRouter(),
        run_repository=repository,
        run_observer=observer,
    )


def test_orchestrator_persists_run_observation() -> None:
    repository = InMemoryResearchRunRepository()
    observer = StubObserver()

    orchestrator = build_orchestrator(
        repository=repository,
        observer=observer,
    )

    result = orchestrator.run(
        ResearchRequest(question="How does operational telemetry improve reliability?")
    )

    persisted_run = repository.list()[0]

    assert result.execution is not None
    assert persisted_run.observation is not None
    assert persisted_run.observation.status == result.execution.status
    assert persisted_run.observation.completed_tasks == result.execution.completed_tasks
    assert persisted_run.observation.failed_tasks == result.execution.failed_tasks
    assert observer.observed_duration is not None
    assert observer.observed_duration >= 0.0
