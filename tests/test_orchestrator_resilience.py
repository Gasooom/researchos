from datetime import UTC, datetime

from app.core.models.research import ResearchRequest, ResearchTask
from app.core.services.claim_grounder import ClaimGrounder
from app.core.services.claim_review import ClaimReviewRouter
from app.core.services.claim_support_classifier import (
    ClaimSupportClassifier,
)
from app.core.services.evidence_extractor import EvidenceExtractor
from app.core.services.orchestrator import ResearchOrchestrator
from app.core.services.reliable_research_agent import ReliableResearchAgent
from app.core.services.research_agent import ResearchAgent
from app.core.services.research_failure import PermanentResearchFailure
from app.core.services.run_executor import ResearchRunExecutor
from app.core.services.source_collector import SourceCollector
from app.core.services.source_deduplicator import SourceDeduplicator
from app.core.services.source_selector import SourceSelector


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
