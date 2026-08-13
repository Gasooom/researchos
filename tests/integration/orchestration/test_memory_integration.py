from datetime import UTC, datetime

from app.application.claims.grounder import ClaimGrounder
from app.application.claims.support_classifier import (
    ClaimSupportClassifier,
)
from app.application.evidence.extractor import EvidenceExtractor
from app.application.memory.research_memory import ResearchMemoryService
from app.application.orchestration.reliable_agent import ReliableResearchAgent
from app.application.orchestration.research import ResearchOrchestrator
from app.application.orchestration.research_agent import ResearchAgent
from app.application.orchestration.run_executor import ResearchRunExecutor
from app.application.retrieval.collector import SourceCollector
from app.application.retrieval.deduplicator import SourceDeduplicator
from app.application.retrieval.selector import SourceSelector
from app.application.retrieval.verifier import SourceVerifier
from app.application.review.router import ClaimReviewRouter
from app.domain.research.models import ResearchRequest, ResearchTask
from app.domain.runs.models import ResearchRunStatus
from app.infrastructure.persistence.in_memory_research_memory import (
    InMemoryResearchMemoryRepository,
)
from app.infrastructure.persistence.in_memory_run_repository import (
    InMemoryResearchRunRepository,
)


class StubPlanner:
    """Deterministic planner for memory integration tests."""

    def plan(self, request: ResearchRequest) -> list[ResearchTask]:
        return [
            ResearchTask(
                objective=request.question,
                task_type="research",
                max_sources=2,
            )
        ]


class StubSearchProvider:
    """Deterministic search provider for memory integration tests."""

    def search(self, query: str) -> list[dict[str, str | float]]:
        return [
            {
                "title": "AI Reliability",
                "url": "https://example.com/reliability",
                "publisher": "example.com",
                "excerpt": "Evaluation improves AI agent reliability.",
                "relevance": 0.92,
            },
            {
                "title": "Agent Evaluation",
                "url": "https://example.org/evaluation",
                "publisher": "example.org",
                "excerpt": "Structured evaluation identifies failures.",
                "relevance": 0.81,
            },
        ]


class StubClock:
    """Deterministic clock for memory integration tests."""

    def now(self) -> datetime:
        return datetime(
            2026,
            8,
            13,
            11,
            0,
            tzinfo=UTC,
        )


def build_orchestrator(
    run_repository: InMemoryResearchRunRepository,
    memory_service: ResearchMemoryService,
) -> ResearchOrchestrator:
    """Build a deterministic memory-aware orchestrator."""
    research_agent = ResearchAgent(StubSearchProvider())
    reliable_agent = ReliableResearchAgent(research_agent)

    return ResearchOrchestrator(
        planner=StubPlanner(),
        run_executor=ResearchRunExecutor(reliable_agent),
        source_collector=SourceCollector(StubClock()),
        source_deduplicator=SourceDeduplicator(),
        source_selector=SourceSelector(max_sources=2),
        source_verifier=SourceVerifier(),
        evidence_extractor=EvidenceExtractor(),
        claim_grounder=ClaimGrounder(),
        claim_support_classifier=ClaimSupportClassifier(),
        claim_review_router=ClaimReviewRouter(),
        run_repository=run_repository,
        memory_service=memory_service,
    )


def test_orchestrator_stores_research_result_in_memory() -> None:
    run_repository = InMemoryResearchRunRepository()
    memory_repository = InMemoryResearchMemoryRepository()
    memory_service = ResearchMemoryService(memory_repository)

    orchestrator = build_orchestrator(
        run_repository=run_repository,
        memory_service=memory_service,
    )

    request = ResearchRequest(
        question="What improves AI agent reliability?",
    )

    result = orchestrator.run(request)

    memory_items = memory_repository.list()

    assert result.execution is not None
    assert result.execution.status == ResearchRunStatus.SUCCESS
    assert len(memory_items) == 1

    memory_item = memory_items[0]

    assert memory_item.question == request.question
    assert memory_item.claims == result.claims
    assert memory_item.evidence
    assert memory_item.summary


def test_orchestrator_retrieves_memory_for_follow_up_run() -> None:
    run_repository = InMemoryResearchRunRepository()
    memory_repository = InMemoryResearchMemoryRepository()
    memory_service = ResearchMemoryService(memory_repository)

    orchestrator = build_orchestrator(
        run_repository=run_repository,
        memory_service=memory_service,
    )

    first_request = ResearchRequest(
        question="What improves AI agent reliability?",
    )

    orchestrator.run(first_request)

    retrieved = memory_service.retrieve(
        question="AI agent reliability",
    )

    assert len(retrieved) == 1
    assert retrieved[0].question == first_request.question


def test_memory_remains_separate_from_fresh_evidence() -> None:
    run_repository = InMemoryResearchRunRepository()
    memory_repository = InMemoryResearchMemoryRepository()
    memory_service = ResearchMemoryService(memory_repository)

    orchestrator = build_orchestrator(
        run_repository=run_repository,
        memory_service=memory_service,
    )

    request = ResearchRequest(
        question="What improves AI agent reliability?",
    )

    result = orchestrator.run(request)

    memory_items = memory_repository.list()

    assert len(memory_items) == 1

    memory_item = memory_items[0]

    assert memory_item.evidence
    assert result.execution is not None
    assert memory_item.evidence != []
