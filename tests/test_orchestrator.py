from datetime import UTC, datetime

from app.core.models.research import (
    ResearchRequest,
    ResearchResult,
    ResearchTask,
)
from app.core.services.claim_grounder import ClaimGrounder
from app.core.services.claim_review import ClaimReviewRouter
from app.core.services.claim_support_classifier import (
    ClaimSupportClassifier,
)
from app.core.services.evidence_extractor import EvidenceExtractor
from app.core.services.orchestrator import ResearchOrchestrator
from app.core.services.reliable_research_agent import ReliableResearchAgent
from app.core.services.research_agent import ResearchAgent
from app.core.services.run_executor import ResearchRunExecutor
from app.core.services.source_collector import SourceCollector
from app.core.services.source_deduplicator import SourceDeduplicator
from app.core.services.source_selector import SourceSelector


class StubPlanner:
    """Deterministic planner for orchestration tests."""

    def plan(self, request: ResearchRequest) -> list[ResearchTask]:
        return [
            ResearchTask(
                objective=request.question,
                task_type="research",
                max_sources=2,
            )
        ]


class StubSearchProvider:
    """Deterministic search provider for orchestration tests."""

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
    """Deterministic clock for orchestration tests."""

    def now(self) -> datetime:
        return datetime(
            2026,
            8,
            12,
            8,
            0,
            tzinfo=UTC,
        )


def build_orchestrator() -> ResearchOrchestrator:
    """Build a fully deterministic research orchestrator."""
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
    )


def test_orchestrator_returns_research_result() -> None:
    orchestrator = build_orchestrator()

    request = ResearchRequest(
        question="What are the main challenges of AI agent reliability?"
    )

    result = orchestrator.run(request)

    assert isinstance(result, ResearchResult)
    assert result.question == request.question
    assert result.sources
    assert result.claims


def test_orchestrator_builds_claims_from_retrieved_evidence() -> None:
    orchestrator = build_orchestrator()

    request = ResearchRequest(
        question="What are the main challenges of AI agent reliability?"
    )

    result = orchestrator.run(request)

    assert len(result.claims) == 2
    assert all(claim.evidence for claim in result.claims)


def test_orchestrator_respects_source_limit() -> None:
    orchestrator = build_orchestrator()

    request = ResearchRequest(
        question="What are the main challenges of AI agent reliability?"
    )

    result = orchestrator.run(request)

    assert len(result.sources) <= 2
