"""Execution quality evaluation for ResearchOS."""

from app.domain.evaluation.models import EvaluationMetric, EvaluationResult
from app.domain.runs.models import ResearchRunOutcome, ResearchRunStatus


class ExecutionQualityEvaluator:
    """Evaluate reliability and completeness of research execution."""

    def evaluate(self, outcome: ResearchRunOutcome) -> EvaluationResult:
        """Compute deterministic execution-quality metrics."""
        total_tasks = outcome.completed_tasks + outcome.failed_tasks

        if total_tasks == 0:
            raise ValueError("research run contains no tasks")

        task_success_rate = outcome.completed_tasks / total_tasks

        failure_rate = outcome.failed_tasks / total_tasks

        partial_run_rate = 1.0 if outcome.status == ResearchRunStatus.PARTIAL else 0.0

        metrics = [
            EvaluationMetric(
                name="task_success_rate",
                value=task_success_rate,
                description=(
                    "Fraction of planned research tasks completed successfully."
                ),
            ),
            EvaluationMetric(
                name="failure_rate",
                value=failure_rate,
                description=("Fraction of planned research tasks that failed."),
            ),
            EvaluationMetric(
                name="partial_run_rate",
                value=partial_run_rate,
                description=("Indicates whether the research run completed partially."),
            ),
        ]

        overall_score = task_success_rate * (1.0 - failure_rate)

        return EvaluationResult(
            metrics=metrics,
            overall_score=overall_score,
        )
