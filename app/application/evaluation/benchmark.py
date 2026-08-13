"""Benchmark aggregation services for ResearchOS."""

from app.domain.evaluation.benchmark import (
    BenchmarkComparison,
    BenchmarkSummary,
)
from app.domain.evaluation.models import EvaluationResult
from app.domain.runs.models import ResearchRunOutcome, ResearchRunStatus


class BenchmarkEvaluator:
    """Aggregate and compare evaluation reports across research runs."""

    def evaluate(
        self,
        reports: list[EvaluationResult],
        outcomes: list[ResearchRunOutcome],
    ) -> BenchmarkSummary:
        """Aggregate quality and execution metrics across runs."""
        if not reports:
            raise ValueError("benchmark requires at least one report")

        if len(reports) != len(outcomes):
            raise ValueError("reports and outcomes must have the same length")

        overall_scores = [report.overall_score for report in reports]

        research_scores = [
            self._metric_value(
                report,
                "overall_research_quality",
            )
            for report in reports
        ]

        execution_scores = [self._execution_score(report) for report in reports]

        semantic_scores = [
            self._metric_value(
                report,
                "semantic_quality",
            )
            for report in reports
        ]

        failure_rate = sum(
            outcome.status == ResearchRunStatus.FAILED for outcome in outcomes
        ) / len(outcomes)

        partial_run_rate = sum(
            outcome.status == ResearchRunStatus.PARTIAL for outcome in outcomes
        ) / len(outcomes)

        return BenchmarkSummary(
            runs_evaluated=len(reports),
            average_overall_score=(sum(overall_scores) / len(overall_scores)),
            average_research_quality=(sum(research_scores) / len(research_scores)),
            average_execution_quality=(sum(execution_scores) / len(execution_scores)),
            average_semantic_quality=(sum(semantic_scores) / len(semantic_scores)),
            failure_rate=failure_rate,
            partial_run_rate=partial_run_rate,
        )

    def compare(
        self,
        baseline: BenchmarkSummary,
        researchos: BenchmarkSummary,
    ) -> BenchmarkComparison:
        """Compare ResearchOS against a baseline benchmark."""
        if baseline.runs_evaluated != researchos.runs_evaluated:
            raise ValueError(
                "baseline and researchos must evaluate the same number of runs"
            )

        return BenchmarkComparison(
            baseline=baseline,
            researchos=researchos,
            overall_score_delta=(
                researchos.average_overall_score - baseline.average_overall_score
            ),
            research_quality_delta=(
                researchos.average_research_quality - baseline.average_research_quality
            ),
            execution_quality_delta=(
                researchos.average_execution_quality
                - baseline.average_execution_quality
            ),
            semantic_quality_delta=(
                researchos.average_semantic_quality - baseline.average_semantic_quality
            ),
            failure_rate_delta=(researchos.failure_rate - baseline.failure_rate),
            partial_run_rate_delta=(
                researchos.partial_run_rate - baseline.partial_run_rate
            ),
        )

    @staticmethod
    def _metric_value(
        report: EvaluationResult,
        metric_name: str,
    ) -> float:
        """Read a named metric from an evaluation report."""
        for metric in report.metrics:
            if metric.name == metric_name:
                return metric.value

        raise ValueError(f"evaluation report missing metric: {metric_name}")

    @staticmethod
    def _execution_score(
        report: EvaluationResult,
    ) -> float:
        """Read the execution-quality score from a report."""
        task_success_rate = BenchmarkEvaluator._metric_value(
            report,
            "task_success_rate",
        )

        failure_rate = BenchmarkEvaluator._metric_value(
            report,
            "failure_rate",
        )

        return task_success_rate * (1.0 - failure_rate)
