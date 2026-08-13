from datetime import UTC, datetime
from pathlib import Path

from app.application.claims.grounder import ClaimGrounder
from app.application.claims.support_classifier import ClaimSupportClassifier
from app.application.evaluation.benchmark import BenchmarkEvaluator
from app.application.evaluation.benchmark_cases import get_benchmark_cases
from app.application.evaluation.benchmark_report import BenchmarkReportBuilder
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


class StubSearchProvider:
    """Deterministic search provider for benchmark experiments."""

    def search(self, query: str) -> list[dict[str, str | float]]:
        return [
            {
                "title": "Benchmark Research Source",
                "url": "https://example.com/benchmark",
                "publisher": "Example Research",
                "excerpt": (
                    "Structured evidence and verification improve research reliability."
                ),
                "relevance": 0.9,
            },
            {
                "title": "Benchmark Evaluation Source",
                "url": "https://example.org/evaluation",
                "publisher": "Example Evaluation",
                "excerpt": ("Independent evaluation helps detect unsupported claims."),
                "relevance": 0.85,
            },
        ]


class StubClock:
    """Deterministic clock for benchmark experiments."""

    def now(self) -> datetime:
        return datetime(
            2026,
            8,
            13,
            16,
            0,
            tzinfo=UTC,
        )


def build_report_builder() -> BenchmarkReportBuilder:
    """Build deterministic benchmark evaluation."""
    research_evaluator = UnifiedResearchEvaluator(
        retrieval_evaluator=RetrievalQualityEvaluator(),
        claim_quality_evaluator=ClaimQualityEvaluator(),
    )

    system_report_builder = EvaluationReportBuilder(
        research_evaluator=research_evaluator,
        execution_evaluator=ExecutionQualityEvaluator(),
    )

    return BenchmarkReportBuilder(
        report_builder=system_report_builder,
        semantic_evaluator=SemanticQualityEvaluator(),
    )


def build_researchos_service(
    tmp_path: Path,
) -> ResearchApplicationService:
    """Build deterministic ResearchOS for benchmark integration."""
    search_provider = StubSearchProvider()

    research_agent = ResearchAgent(search_provider)
    reliable_agent = ReliableResearchAgent(research_agent)

    memory_repository = InMemoryResearchMemoryRepository()
    memory_service = ResearchMemoryService(memory_repository)

    orchestrator = ResearchOrchestrator(
        planner=DeterministicPlanner(),
        run_executor=ResearchRunExecutor(
            reliable_agent,
        ),
        source_collector=SourceCollector(StubClock()),
        source_deduplicator=SourceDeduplicator(),
        source_selector=SourceSelector(max_sources=3),
        source_verifier=SourceVerifier(),
        evidence_extractor=EvidenceExtractor(),
        claim_grounder=ClaimGrounder(),
        claim_support_classifier=ClaimSupportClassifier(),
        claim_review_router=ClaimReviewRouter(),
        run_repository=None,
        run_observer=None,
        memory_service=memory_service,
    )

    return ResearchApplicationService(orchestrator)


def test_researchos_benchmark_runs_all_cases(
    tmp_path: Path,
) -> None:
    runner = ResearchOSBenchmarkRunner(
        service=build_researchos_service(tmp_path),
        report_builder=build_report_builder(),
    )

    reports = []
    outcomes = []

    for case in get_benchmark_cases():
        result, report = runner.run(case)

        reports.append(report)

        assert result.execution is not None
        outcomes.append(result.execution)

    summary = BenchmarkEvaluator().evaluate(
        reports=reports,
        outcomes=outcomes,
    )

    assert summary.runs_evaluated == len(get_benchmark_cases())
    assert 0.0 <= summary.average_overall_score <= 1.0
    assert 0.0 <= summary.average_research_quality <= 1.0
    assert 0.0 <= summary.average_execution_quality <= 1.0
    assert 0.0 <= summary.average_semantic_quality <= 1.0
