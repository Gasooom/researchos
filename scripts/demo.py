"""Deterministic end-to-end demo for ResearchOS."""

from datetime import UTC, datetime

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
from app.domain.research.models import ResearchRequest
from app.infrastructure.persistence.in_memory_run_repository import (
    InMemoryResearchRunRepository,
)
from app.infrastructure.telemetry.run_observer import RunObserver


class DemoSearchProvider:
    """Deterministic search provider for the local demo."""

    def search(self, query: str) -> list[dict[str, str | float]]:
        return [
            {
                "title": "AI Reliability Research",
                "url": "https://example.com/ai-reliability",
                "publisher": "Example Research",
                "excerpt": (
                    "Evidence-grounded AI systems benefit from "
                    "structured evaluation and traceable execution."
                ),
                "relevance": 0.95,
            },
            {
                "title": "Multi-Agent Systems",
                "url": "https://example.com/multi-agent-systems",
                "publisher": "Example Research",
                "excerpt": (
                    "Specialized agents can separate retrieval, analysis, "
                    "and synthesis responsibilities."
                ),
                "relevance": 0.91,
            },
        ]


class DemoClock:
    """Deterministic clock for the demo."""

    def now(self) -> datetime:
        return datetime(
            2026,
            8,
            13,
            11,
            0,
            tzinfo=UTC,
        )


def build_demo_service() -> tuple[
    ResearchApplicationService,
    InMemoryResearchRunRepository,
]:
    """Build a complete deterministic ResearchOS workflow."""
    repository = InMemoryResearchRunRepository()

    research_agent = ResearchAgent(
        search_provider=DemoSearchProvider(),
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
            clock=DemoClock(),
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

    return service, repository


def main() -> None:
    """Run a complete ResearchOS demonstration."""
    print("=" * 64)
    print("ResearchOS - End-to-End Demo")
    print("=" * 64)

    question = "How do multi-agent systems improve research reliability?"

    service, repository = build_demo_service()

    print("\nQUESTION")
    print("-" * 64)
    print(question)

    result = service.execute(
        ResearchRequest(
            question=question,
            max_sources=2,
        )
    )

    print("\nEXECUTION")
    print("-" * 64)

    if result.execution is not None:
        print(f"Status:          {result.execution.status.value}")
        print(f"Tasks completed: {result.execution.completed_tasks}")
        print(f"Tasks failed:    {result.execution.failed_tasks}")

    print("\nRESEARCH ARTIFACTS")
    print("-" * 64)
    print(f"Sources: {len(result.sources)}")
    print(f"Claims:  {len(result.claims)}")

    print("\nSOURCES")
    print("-" * 64)

    for index, source in enumerate(result.sources, start=1):
        print(f"{index}. {source.title}")
        print(f"   {source.url}")

    print("\nUNIQUE CLAIMS")
    print("-" * 64)

    seen_claims: set[str] = set()

    for claim in result.claims:
        statement = claim.statement

        if statement in seen_claims:
            continue

        seen_claims.add(statement)
        print(f"- {statement}")

    persisted_runs = repository.list()

    print("\nOBSERVABILITY")
    print("-" * 64)

    if persisted_runs:
        run = persisted_runs[-1]

        print(f"Run ID:      {run.id}")
        print(f"Completed:   {run.completed_at is not None}")

        if run.observation is not None:
            print(f"Duration:    {run.observation.duration_seconds:.4f}s")
            print(f"Total tasks: {run.observation.total_tasks}")
            print(f"Completed:   {run.observation.completed_tasks}")
            print(f"Failed:      {run.observation.failed_tasks}")
            print(f"Status:      {run.observation.status.value}")

    print("\n" + "=" * 64)
    print("Demo completed successfully.")
    print("=" * 64)


if __name__ == "__main__":
    main()
