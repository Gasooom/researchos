"""Benchmark comparison experiments for ResearchOS."""

from datetime import UTC, datetime

from app.application.agents.analysis import AnalysisAgent
from app.application.agents.retrieval import RetrievalAgent
from app.application.agents.synthesis import SynthesisAgent
from app.application.claims.grounder import ClaimGrounder
from app.application.claims.support_classifier import ClaimSupportClassifier
from app.application.evaluation.benchmark import BenchmarkEvaluator
from app.application.evaluation.benchmark_cases import get_benchmark_cases
from app.application.evaluation.benchmark_report import BenchmarkReportBuilder
from app.application.evaluation.benchmark_runner import (
    BaselineResearchRunner,
)
from app.application.evaluation.claims import ClaimQualityEvaluator
from app.application.evaluation.execution import ExecutionQualityEvaluator
from app.application.evaluation.report import EvaluationReportBuilder
from app.application.evaluation.research import UnifiedResearchEvaluator
from app.application.evaluation.researchos_benchmark import (
    ResearchOSBenchmarkRunner,
)
from app.application.evaluation.retrieval import RetrievalQualityEvaluator
from app.application.evaluation.semantic import SemanticQualityEvaluator
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
from app.infrastructure.persistence.in_memory_research_memory import (
    InMemoryResearchMemoryRepository,
)


class BenchmarkSearchProvider:
    """Deterministic search provider shared by both systems."""

    def search(
        self,
        query: str,
    ) -> list[dict[str, str | float]]:
        """Return identical deterministic evidence for a query."""
        return [
            {
                "title": "Benchmark Reliability Source",
                "url": "https://example.com/reliability",
                "publisher": "Example Research",
                "excerpt": (
                    "Specialized research roles can improve reliability "
                    "through focused retrieval and verification."
                ),
                "relevance": 0.90,
            },
            {
                "title": "Benchmark Evaluation Source",
                "url": "https://example.org/evaluation",
                "publisher": "Example Evaluation",
                "excerpt": (
                    "Independent evaluation can identify unsupported research claims."
                ),
                "relevance": 0.85,
            },
        ]


class BenchmarkClock:
    """Deterministic clock for benchmark experiments."""

    def now(self) -> datetime:
        """Return a fixed timestamp."""
        return datetime(
            2026,
            8,
            13,
            16,
            0,
            tzinfo=UTC,
        )


class ResearchOSBenchmarkEnvironment:
    """Build the deterministic multi-agent ResearchOS environment."""

    def __init__(self) -> None:
        self.search_provider = BenchmarkSearchProvider()

        # Baseline research agent.
        research_agent = ResearchAgent(
            self.search_provider,
        )

        reliable_agent = ReliableResearchAgent(
            research_agent,
        )

        # Actual multi-agent ResearchOS stack.
        retrieval_agent = RetrievalAgent(
            search_provider=self.search_provider,
        )

        analysis_agent = AnalysisAgent()

        synthesis_agent = SynthesisAgent()

        multi_agent_coordinator = MultiAgentCoordinator(
            retrieval_agent=retrieval_agent,
            analysis_agent=analysis_agent,
            synthesis_agent=synthesis_agent,
        )

        # Research memory.
        memory_repository = InMemoryResearchMemoryRepository()

        memory_service = ResearchMemoryService(
            memory_repository,
        )

        orchestrator = ResearchOrchestrator(
            planner=DeterministicPlanner(),
            run_executor=ResearchRunExecutor(
                reliable_agent,
            ),
            source_collector=SourceCollector(
                BenchmarkClock(),
            ),
            source_deduplicator=SourceDeduplicator(),
            source_selector=SourceSelector(
                max_sources=3,
            ),
            source_verifier=SourceVerifier(),
            evidence_extractor=EvidenceExtractor(),
            claim_grounder=ClaimGrounder(),
            claim_support_classifier=ClaimSupportClassifier(),
            claim_review_router=ClaimReviewRouter(),
            multi_agent_coordinator=multi_agent_coordinator,
            run_repository=None,
            run_observer=None,
            memory_service=memory_service,
        )

        self.service = ResearchApplicationService(
            orchestrator,
        )


def build_system_report_builder() -> EvaluationReportBuilder:
    """Build deterministic system evaluation."""
    return EvaluationReportBuilder(
        research_evaluator=UnifiedResearchEvaluator(
            retrieval_evaluator=RetrievalQualityEvaluator(),
            claim_quality_evaluator=ClaimQualityEvaluator(),
        ),
        execution_evaluator=ExecutionQualityEvaluator(),
    )


def build_benchmark_report_builder() -> BenchmarkReportBuilder:
    """Build benchmark-aware evaluation."""
    return BenchmarkReportBuilder(
        report_builder=build_system_report_builder(),
        semantic_evaluator=SemanticQualityEvaluator(),
    )


def run_benchmark_comparison():
    """Run benchmark cases against baseline and ResearchOS."""
    environment = ResearchOSBenchmarkEnvironment()

    report_builder = build_benchmark_report_builder()

    baseline_runner = BaselineResearchRunner(
        research_agent=ResearchAgent(
            environment.search_provider,
        ),
        report_builder=report_builder,
    )

    researchos_runner = ResearchOSBenchmarkRunner(
        service=environment.service,
        report_builder=report_builder,
    )

    baseline_reports = []
    baseline_outcomes = []

    researchos_reports = []
    researchos_outcomes = []

    for case in get_benchmark_cases():
        baseline_result, baseline_report = baseline_runner.run(case)

        researchos_execution, researchos_report = researchos_runner.run(case)

        if baseline_result.execution is None:
            raise ValueError("baseline benchmark result has no execution outcome")

        if researchos_execution.execution is None:
            raise ValueError("ResearchOS benchmark result has no execution outcome")

        baseline_reports.append(
            baseline_report,
        )
        baseline_outcomes.append(
            baseline_result.execution,
        )

        researchos_reports.append(
            researchos_report,
        )
        researchos_outcomes.append(
            researchos_execution.execution,
        )

    evaluator = BenchmarkEvaluator()

    baseline_summary = evaluator.evaluate(
        reports=baseline_reports,
        outcomes=baseline_outcomes,
    )

    researchos_summary = evaluator.evaluate(
        reports=researchos_reports,
        outcomes=researchos_outcomes,
    )

    return evaluator.compare(
        baseline=baseline_summary,
        researchos=researchos_summary,
    )
