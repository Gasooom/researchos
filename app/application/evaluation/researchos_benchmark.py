"""ResearchOS benchmark execution services."""

from app.application.evaluation.benchmark_report import (
    BenchmarkReportBuilder,
)
from app.application.research_service import ResearchApplicationService
from app.domain.evaluation.benchmark import (
    BenchmarkCase,
    BenchmarkExecutionResult,
)
from app.domain.evaluation.models import EvaluationResult
from app.domain.research.models import ResearchRequest


class ResearchOSBenchmarkRunner:
    """Run benchmark cases through the production ResearchOS workflow."""

    def __init__(
        self,
        service: ResearchApplicationService,
        report_builder: BenchmarkReportBuilder,
    ) -> None:
        self.service = service
        self.report_builder = report_builder

    def run(
        self,
        case: BenchmarkCase,
    ) -> tuple[BenchmarkExecutionResult, EvaluationResult]:
        """Run one benchmark case through ResearchOS."""
        (
            result,
            _outcome,
            multi_agent_results,
        ) = self.service.execute_with_evaluation_artifacts(
            ResearchRequest(
                question=case.question,
                max_sources=3,
            )
        )

        if result.execution is None:
            raise ValueError("ResearchOS benchmark result has no execution outcome")

        execution = BenchmarkExecutionResult(
            result=result,
            multi_agent_results=multi_agent_results,
        )

        report = self.report_builder.build(
            case=case,
            result=execution.result,
            multi_agent_results=execution.multi_agent_results,
        )

        return execution, report
