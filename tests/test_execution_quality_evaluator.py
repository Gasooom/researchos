import pytest

from app.core.models.run import (
    ResearchRunFailure,
    ResearchRunOutcome,
    ResearchRunStatus,
)
from app.core.services.execution_quality_evaluator import (
    ExecutionQualityEvaluator,
)


def make_outcome(
    status: ResearchRunStatus,
    completed_tasks: int,
    failed_tasks: int,
) -> ResearchRunOutcome:
    failures = [
        ResearchRunFailure(
            task_objective=f"task {index}",
            error_type="RuntimeError",
            message="task failed",
        )
        for index in range(failed_tasks)
    ]

    return ResearchRunOutcome(
        status=status,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
        failures=failures,
    )


def test_execution_evaluator_calculates_success_rate() -> None:
    evaluator = ExecutionQualityEvaluator()

    outcome = make_outcome(
        ResearchRunStatus.SUCCESS,
        completed_tasks=4,
        failed_tasks=0,
    )

    evaluation = evaluator.evaluate(outcome)

    metrics = {metric.name: metric.value for metric in evaluation.metrics}

    assert metrics["task_success_rate"] == pytest.approx(1.0)
    assert metrics["failure_rate"] == pytest.approx(0.0)
    assert metrics["partial_run_rate"] == pytest.approx(0.0)
    assert evaluation.overall_score == pytest.approx(1.0)


def test_execution_evaluator_detects_partial_run() -> None:
    evaluator = ExecutionQualityEvaluator()

    outcome = make_outcome(
        ResearchRunStatus.PARTIAL,
        completed_tasks=2,
        failed_tasks=1,
    )

    evaluation = evaluator.evaluate(outcome)

    metrics = {metric.name: metric.value for metric in evaluation.metrics}

    assert metrics["task_success_rate"] == pytest.approx(2 / 3)
    assert metrics["failure_rate"] == pytest.approx(1 / 3)
    assert metrics["partial_run_rate"] == pytest.approx(1.0)
    assert evaluation.overall_score == pytest.approx(4 / 9)


def test_execution_evaluator_detects_failed_run() -> None:
    evaluator = ExecutionQualityEvaluator()

    outcome = make_outcome(
        ResearchRunStatus.FAILED,
        completed_tasks=0,
        failed_tasks=3,
    )

    evaluation = evaluator.evaluate(outcome)

    metrics = {metric.name: metric.value for metric in evaluation.metrics}

    assert metrics["task_success_rate"] == pytest.approx(0.0)
    assert metrics["failure_rate"] == pytest.approx(1.0)
    assert metrics["partial_run_rate"] == pytest.approx(0.0)
    assert evaluation.overall_score == pytest.approx(0.0)


def test_execution_evaluator_rejects_zero_tasks() -> None:
    evaluator = ExecutionQualityEvaluator()

    outcome = make_outcome(
        ResearchRunStatus.SUCCESS,
        completed_tasks=0,
        failed_tasks=0,
    )

    with pytest.raises(
        ValueError,
        match="research run contains no tasks",
    ):
        evaluator.evaluate(outcome)
