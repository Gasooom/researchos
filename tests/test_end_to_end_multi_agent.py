from datetime import UTC, datetime

from app.core.models.research import ResearchRequest
from app.core.services.analysis_agent import AnalysisAgent
from app.core.services.claim_grounder import ClaimGrounder
from app.core.services.claim_review import ClaimReviewRouter
from app.core.services.claim_support_classifier import (
    ClaimSupportClassifier,
)
from app.core.services.evidence_extractor import EvidenceExtractor
from app.core.services.multi_agent_coordinator import MultiAgentCoordinator
from app.core.services.orchestrator import ResearchOrchestrator
from app.core.services.retrieval_agent import RetrievalAgent
from app.core.services.run_executor import ResearchRunExecutor
from app.core.services.source_collector import SourceCollector
from app.core.services.source_deduplicator import SourceDeduplicator
from app.core.services.source_selector import SourceSelector
from app.core.services.synthesis_agent import SynthesisAgent


class StubSearchProvider:
    """Deterministic search provider for the end-to-end test."""

    def search(self, query: str) -> list[dict[str, str | float]]:
        return [
            {
                "title": "AI Reliability Research",
                "url": "https://example.com/reliability",
                "publisher": "Example Research",
                "excerpt": "AI agents can fail unpredictably.",
                "relevance": 0.94,
            },
            {
                "title": "Agent Evaluation Study",
                "url": "https://example.com/evaluation",
                "publisher": "Example Research",
                "excerpt": "Evaluation improves agent reliability.",
                "relevance": 0.88,
            },
        ]


class StubPlanner:
    """Deterministic planner producing one research task."""

    def plan(self, request: ResearchRequest):
        from app.core.models.research import ResearchTask

        return [
            ResearchTask(
                objective=request.question,
                task_type="research",
                max_sources=5,
            )
        ]


class StubClock:
    """Deterministic clock for source collection."""

    def now(self) -> datetime:
        return datetime(
            2026,
            8,
            12,
            9,
            0,
            tzinfo=UTC,
        )


def build_orchestrator() -> ResearchOrchestrator:
    search_provider = StubSearchProvider()

    retrieval_agent = RetrievalAgent(
        search_provider=search_provider,
    )
    analysis_agent = AnalysisAgent()
    synthesis_agent = SynthesisAgent()

    coordinator = MultiAgentCoordinator(
        retrieval_agent=retrieval_agent,
        analysis_agent=analysis_agent,
        synthesis_agent=synthesis_agent,
    )

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
        multi_agent_coordinator=coordinator,
    )


def test_end_to_end_multi_agent_research() -> None:
    orchestrator = build_orchestrator()

    result = orchestrator.run(
        ResearchRequest(
            question="What improves AI agent reliability?",
        )
    )

    assert result.question == "What improves AI agent reliability?"

    assert result.execution is not None
    assert result.execution.status.value == "success"
    assert result.execution.completed_tasks == 1
    assert result.execution.failed_tasks == 0

    assert len(result.sources) == 2
    assert len(result.claims) == 2

    assert result.claims[0].evidence
    assert result.claims[1].evidence

    excerpts = {claim.evidence[0].excerpt for claim in result.claims}

    assert excerpts == {
        "AI agents can fail unpredictably.",
        "Evaluation improves agent reliability.",
    }


def test_end_to_end_multi_agent_preserves_relevance() -> None:
    orchestrator = build_orchestrator()

    result = orchestrator.run(
        ResearchRequest(
            question="What improves AI agent reliability?",
        )
    )

    relevance_scores = [claim.evidence[0].relevance for claim in result.claims]

    assert relevance_scores == [0.94, 0.88]
