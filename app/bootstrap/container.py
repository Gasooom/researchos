"""Application composition root for ResearchOS."""

from datetime import UTC, datetime

from app.application.agents.analysis import AnalysisAgent
from app.application.agents.llm_analysis import LLMAnalysisAgent
from app.application.agents.llm_synthesis import LLMSynthesisAgent
from app.application.agents.retrieval import RetrievalAgent
from app.application.agents.synthesis import SynthesisAgent
from app.application.claims.grounder import ClaimGrounder
from app.application.claims.support_classifier import (
    ClaimSupportClassifier,
)
from app.application.evidence.extractor import EvidenceExtractor
from app.application.memory.research_memory import ResearchMemoryService
from app.application.orchestration.multi_agent import MultiAgentCoordinator
from app.application.orchestration.planning import DeterministicPlanner
from app.application.orchestration.reliable_agent import ReliableResearchAgent
from app.application.orchestration.research import ResearchOrchestrator
from app.application.orchestration.research_agent import ResearchAgent
from app.application.orchestration.run_executor import ResearchRunExecutor
from app.application.research_service import ResearchApplicationService
from app.application.retrieval.collector import SourceCollector
from app.application.retrieval.deduplicator import SourceDeduplicator
from app.application.retrieval.selector import SourceSelector
from app.application.retrieval.verifier import SourceVerifier
from app.application.review.router import ClaimReviewRouter
from app.core.config import Settings, get_settings
from app.infrastructure.llm.factory import create_llm_provider
from app.infrastructure.persistence.in_memory_research_memory import (
    InMemoryResearchMemoryRepository,
)
from app.infrastructure.persistence.sqlite_run_repository import (
    SQLiteResearchRunRepository,
)
from app.infrastructure.search.provider import SearchProvider
from app.infrastructure.search.tavily import create_tavily_search_provider
from app.infrastructure.telemetry.run_observer import RunObserver


class SystemClock:
    """Production clock using the current UTC time."""

    def now(self) -> datetime:
        """Return the current UTC timestamp."""
        return datetime.now(UTC)


def create_research_service(
    settings: Settings | None = None,
    search_provider: SearchProvider | None = None,
) -> ResearchApplicationService:
    """Build the production ResearchOS application service."""
    settings = settings or get_settings()

    search_provider = search_provider or create_tavily_search_provider(
        settings,
    )

    research_agent = ResearchAgent(search_provider)

    reliable_research_agent = ReliableResearchAgent(
        research_agent,
    )

    retrieval_agent = RetrievalAgent(search_provider)

    if settings.llm_mode == "openai":
        llm_provider = create_llm_provider(settings)

        analysis_agent = LLMAnalysisAgent(
            provider=llm_provider,
        )

        synthesis_agent = LLMSynthesisAgent(
            provider=llm_provider,
        )
    elif settings.llm_mode == "deterministic":
        analysis_agent = AnalysisAgent()
        synthesis_agent = SynthesisAgent()
    else:
        raise ValueError("LLM_MODE must be either 'deterministic' or 'openai'.")

    multi_agent_coordinator = MultiAgentCoordinator(
        retrieval_agent=retrieval_agent,
        analysis_agent=analysis_agent,
        synthesis_agent=synthesis_agent,
    )

    run_executor = ResearchRunExecutor(
        research_agent=reliable_research_agent,
    )

    run_repository = SQLiteResearchRunRepository(
        database_path=settings.research_database_path,
    )

    memory_repository = InMemoryResearchMemoryRepository()
    memory_service = ResearchMemoryService(memory_repository)

    orchestrator = ResearchOrchestrator(
        planner=DeterministicPlanner(),
        run_executor=run_executor,
        source_collector=SourceCollector(SystemClock()),
        source_deduplicator=SourceDeduplicator(),
        source_selector=SourceSelector(max_sources=5),
        source_verifier=SourceVerifier(),
        evidence_extractor=EvidenceExtractor(),
        claim_grounder=ClaimGrounder(),
        claim_support_classifier=ClaimSupportClassifier(),
        claim_review_router=ClaimReviewRouter(),
        multi_agent_coordinator=multi_agent_coordinator,
        run_repository=run_repository,
        run_observer=RunObserver(),
        memory_service=memory_service,
    )

    return ResearchApplicationService(
        orchestrator,
    )
