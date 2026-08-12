"""Benchmark aggregation services for ResearchOS."""

from app.core.models.benchmark import BenchmarkSummary
from app.core.models.evaluation import EvaluationResult
from app.core.models.run import ResearchRunOutcome, ResearchRunStatus


class BenchmarkEvaluator:
    """Aggregate evaluation reports across multiple research runs."""

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

        execution_scores = [
            self._execution_score(
                report,
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
            average_overall_score=sum(overall_scores) / len(overall_scores),
            average_research_quality=sum(research_scores) / len(research_scores),
            average_execution_quality=sum(execution_scores) / len(execution_scores),
            failure_rate=failure_rate,
            partial_run_rate=partial_run_rate,
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
    def _execution_score(report: EvaluationResult) -> float:
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
