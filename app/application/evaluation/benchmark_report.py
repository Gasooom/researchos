"""Benchmark-specific evaluation report services."""

from app.application.evaluation.report import EvaluationReportBuilder
from app.application.evaluation.semantic import SemanticQualityEvaluator
from app.domain.evaluation.benchmark import (
    BenchmarkCase,
    BenchmarkEvaluationInput,
)
from app.domain.evaluation.models import EvaluationMetric, EvaluationResult
from app.domain.research.models import ResearchResult
from app.domain.research.multi_agent import MultiAgentResearchResult


class BenchmarkReportBuilder:
    """Combine system evaluation with benchmark-specific semantics."""

    def __init__(
        self,
        report_builder: EvaluationReportBuilder,
        semantic_evaluator: SemanticQualityEvaluator,
    ) -> None:
        self.report_builder = report_builder
        self.semantic_evaluator = semantic_evaluator

    def build(
        self,
        case: BenchmarkCase,
        result: ResearchResult,
        multi_agent_results: list[MultiAgentResearchResult] | None = None,
    ) -> EvaluationResult:
        """Build a benchmark-aware evaluation report."""
        system_report = self.report_builder.build(result)

        semantic_report = self.semantic_evaluator.evaluate(
            BenchmarkEvaluationInput(
                case=case,
                result=result,
                multi_agent_results=multi_agent_results or [],
            )
        )

        metrics = [
            *system_report.metrics,
            *semantic_report.metrics,
            EvaluationMetric(
                name="semantic_quality",
                value=semantic_report.overall_score,
                description=("Benchmark-specific semantic quality score."),
            ),
        ]

        return EvaluationResult(
            metrics=metrics,
            overall_score=system_report.overall_score,
        )
