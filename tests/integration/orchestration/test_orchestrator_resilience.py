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
from app.domain.runs.failures import PermanentResearchFailure


class StubPlanner:
    def plan(self, request: ResearchRequest) -> list[ResearchTask]:
        return [
            ResearchTask(
                objective="successful research task",
                task_type="research",
                max_sources=2,
            ),
            ResearchTask(
                objective="failing research task",
                task_type="research",
                max_sources=2,
            ),
            ResearchTask(
                objective="another successful task",
                task_type="research",
                max_sources=2,
            ),
        ]


class ResilientSearchProvider:
    def search(self, query: str) -> list[dict[str, str | float]]:
        if query == "failing research task":
            raise PermanentResearchFailure("provider unavailable")

        return [
            {
                "title": f"{query} source",
                "url": f"https://example.com/{query.replace(' ', '-')}",
                "publisher": "example.com",
                "excerpt": f"Evidence for {query}.",
                "relevance": 0.9,
            }
        ]


class StubClock:
    def now(self) -> datetime:
        return datetime(
            2026,
            8,
            12,
            9,
            0,
            tzinfo=UTC,
        )


class FailingAwareResearchAgent(ResearchAgent):
    def research(self, task: ResearchTask):
        if task.objective == "failing research task":
            raise PermanentResearchFailure("provider unavailable")

        return super().research(task)


def build_orchestrator() -> ResearchOrchestrator:
    research_agent = FailingAwareResearchAgent(ResilientSearchProvider())
    reliable_agent = ReliableResearchAgent(research_agent)

    return ResearchOrchestrator(
        planner=StubPlanner(),
        run_executor=ResearchRunExecutor(reliable_agent),
        source_collector=SourceCollector(StubClock()),
        source_deduplicator=SourceDeduplicator(),
        source_selector=SourceSelector(max_sources=5),
        evidence_extractor=EvidenceExtractor(),
        claim_grounder=ClaimGrounder(),
        claim_support_classifier=ClaimSupportClassifier(),
        claim_review_router=ClaimReviewRouter(),
    )


def test_orchestrator_preserves_successful_work_after_task_failure() -> None:
    orchestrator = build_orchestrator()

    result = orchestrator.run(
        ResearchRequest(
            question="What are the main challenges of AI agent reliability?"
        )
    )

    assert result.sources
    assert result.claims
    assert len(result.claims) == 2
