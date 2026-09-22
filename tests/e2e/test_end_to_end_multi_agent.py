from datetime import UTC, datetime

from app.application.agents.analysis import AnalysisAgent
from app.application.agents.retrieval import RetrievalAgent
from app.application.agents.synthesis import SynthesisAgent
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
from app.domain.research.models import ResearchRequest


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
        from app.domain.research.models import ResearchTask

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

    # Since M6 each synthesized claim carries the full evidence set for its
    # task, rather than one excerpt per claim, so excerpts are checked across
    # all attached evidence.
    excerpts = {
        evidence.excerpt for claim in result.claims for evidence in claim.evidence
    }

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

    scores = {
        evidence.relevance for claim in result.claims for evidence in claim.evidence
    }

    relevance_scores = sorted(scores, reverse=True)

    assert relevance_scores == [0.94, 0.88]


def test_deterministic_agents_still_derive_statements_from_excerpts() -> None:
    """Honest limit of M6: independence depends on the analysis agent.

    The offline AnalysisAgent sets key_points to the evidence excerpts verbatim
    and SynthesisAgent passes them through, so claim statements on the
    deterministic path remain copies of their evidence. Independence is real
    only for the LLM-backed agents used when LLM_MODE=openai, which is what the
    benchmark exercises. This test records that boundary rather than implying
    the whole system produces independent claims.
    """
    orchestrator = build_orchestrator()

    result = orchestrator.run(
        ResearchRequest(
            question="What improves AI agent reliability?",
        )
    )

    excerpts = {
        evidence.excerpt for claim in result.claims for evidence in claim.evidence
    }

    assert {claim.statement for claim in result.claims} <= excerpts
