from datetime import UTC, datetime

from app.application.claims.grounder import ClaimGrounder
from app.application.claims.support_classifier import (
    ClaimSupportClassifier,
)
from app.application.evidence.extractor import EvidenceExtractor
from app.application.orchestration.multi_agent import MultiAgentCoordinator
from app.application.orchestration.research import ResearchOrchestrator
from app.application.orchestration.run_executor import ResearchRunExecutor
from app.application.retrieval.collector import SourceCollector
from app.application.retrieval.deduplicator import SourceDeduplicator
from app.application.retrieval.selector import SourceSelector
from app.application.review.router import ClaimReviewRouter
from app.domain.research.analysis import AnalysisResult
from app.domain.research.models import (
    Evidence,
    ResearchRequest,
    ResearchTask,
    Source,
)
from app.domain.research.multi_agent import MultiAgentResearchResult
from app.domain.research.synthesis import SynthesisResult
from app.infrastructure.persistence.in_memory_run_repository import (
    InMemoryResearchRunRepository,
)


class StubPlanner:
    """Deterministic planner for multi-agent orchestration tests."""

    def plan(self, request: ResearchRequest) -> list[ResearchTask]:
        return [
            ResearchTask(
                objective="Research reliability",
                task_type="research",
                max_sources=2,
            ),
            ResearchTask(
                objective="Research evaluation",
                task_type="research",
                max_sources=2,
            ),
            ResearchTask(
                objective="Research deployment",
                task_type="research",
                max_sources=2,
            ),
        ]


class StubCoordinator(MultiAgentCoordinator):
    """Deterministic coordinator with optional task failures."""

    def __init__(
        self,
        failing_objectives: set[str] | None = None,
    ) -> None:
        self.failing_objectives = failing_objectives or set()

    def execute(
        self,
        task: ResearchTask,
    ) -> MultiAgentResearchResult:
        if task.objective in self.failing_objectives:
            raise RuntimeError(f"failed task: {task.objective}")

        source = Source(
            title=f"{task.objective} Source",
            url=(f"https://example.com/{task.objective.lower().replace(' ', '-')}"),
            publisher="Example Research",
            retrieved_at=datetime.now(UTC),
        )

        evidence = Evidence(
            source=source,
            excerpt=f"Evidence for {task.objective}.",
            relevance=0.94,
        )

        analysis = AnalysisResult(
            summary=f"Analysis for {task.objective}.",
            key_points=[
                f"Key point for {task.objective}.",
            ],
            confidence=0.94,
        )

        synthesis = SynthesisResult(
            answer=f"Synthesis for {task.objective}.",
            supporting_points=[
                f"Key point for {task.objective}.",
            ],
            confidence=0.94,
        )

        return MultiAgentResearchResult(
            evidence=[evidence],
            analysis=analysis,
            synthesis=synthesis,
        )


class StubClock:
    """Deterministic clock for orchestration tests."""

    def now(self) -> datetime:
        return datetime(
            2026,
            8,
            12,
            9,
            0,
            tzinfo=UTC,
        )


def build_orchestrator(
    failing_objectives: set[str] | None = None,
    run_repository: InMemoryResearchRunRepository | None = None,
) -> ResearchOrchestrator:
    return ResearchOrchestrator(
        planner=StubPlanner(),
        run_executor=ResearchRunExecutor(
            research_agent=None,  # type: ignore[arg-type]
        ),
        source_collector=SourceCollector(StubClock()),
        source_deduplicator=SourceDeduplicator(),
        source_selector=SourceSelector(max_sources=5),
        evidence_extractor=EvidenceExtractor(),
        claim_grounder=ClaimGrounder(),
        claim_support_classifier=ClaimSupportClassifier(),
        claim_review_router=ClaimReviewRouter(),
        multi_agent_coordinator=StubCoordinator(
            failing_objectives=failing_objectives,
        ),
        run_repository=run_repository,
    )


def test_orchestrator_executes_all_multi_agent_tasks() -> None:
    orchestrator = build_orchestrator()

    result = orchestrator.run(
        ResearchRequest(question="Multi-agent research"),
    )

    assert result.execution is not None
    assert result.execution.status.value == "success"
    assert result.execution.completed_tasks == 3
    assert result.execution.failed_tasks == 0
    assert len(result.execution.evidence) == 3
    assert len(result.sources) == 3
    assert len(result.claims) == 3


def test_orchestrator_preserves_successful_tasks_after_failure() -> None:
    orchestrator = build_orchestrator(
        {"Research evaluation"},
    )

    result = orchestrator.run(
        ResearchRequest(question="Multi-agent research"),
    )

    assert result.execution is not None
    assert result.execution.status.value == "partial"
    assert result.execution.completed_tasks == 2
    assert result.execution.failed_tasks == 1
    assert len(result.execution.failures) == 1
    assert result.execution.failures[0].task_objective == ("Research evaluation")
    assert len(result.execution.evidence) == 2
    assert len(result.claims) == 2


def test_orchestrator_records_multi_agent_failure_details() -> None:
    orchestrator = build_orchestrator(
        {"Research deployment"},
    )

    result = orchestrator.run(
        ResearchRequest(question="Multi-agent research"),
    )

    failure = result.execution.failures[0]

    assert failure.error_type == "RuntimeError"
    assert failure.message == "failed task: Research deployment"


def test_orchestrator_persists_partial_multi_agent_run() -> None:
    repository = InMemoryResearchRunRepository()

    orchestrator = build_orchestrator(
        {"Research evaluation"},
        run_repository=repository,
    )

    result = orchestrator.run(
        ResearchRequest(question="Multi-agent research"),
    )

    persisted_runs = repository.list()

    assert len(persisted_runs) == 1

    persisted_run = persisted_runs[0]

    assert persisted_run.completed_at is not None
    assert persisted_run.outcome == result.execution
    assert persisted_run.outcome.status.value == "partial"
    assert persisted_run.outcome.completed_tasks == 2
    assert persisted_run.outcome.failed_tasks == 1
