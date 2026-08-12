import pytest

from app.domain.runs.models import ResearchRunOutcome, ResearchRunStatus
from app.infrastructure.telemetry.run_observer import RunObserver


def make_outcome(
    status: ResearchRunStatus,
    completed_tasks: int,
    failed_tasks: int,
) -> ResearchRunOutcome:
    return ResearchRunOutcome(
        status=status,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
    )


def test_run_observer_records_execution_metrics() -> None:
    observer = RunObserver()

    observation = observer.observe(
        outcome=make_outcome(
            status=ResearchRunStatus.SUCCESS,
            completed_tasks=4,
            failed_tasks=0,
        ),
        duration_seconds=2.5,
    )

    assert observation.duration_seconds == 2.5
    assert observation.total_tasks == 4
    assert observation.completed_tasks == 4
    assert observation.failed_tasks == 0
    assert observation.status == ResearchRunStatus.SUCCESS


def test_run_observer_calculates_success_rate() -> None:
    observer = RunObserver()

    observation = observer.observe(
        outcome=make_outcome(
            status=ResearchRunStatus.PARTIAL,
            completed_tasks=2,
            failed_tasks=1,
        ),
        duration_seconds=3.0,
    )

    assert observation.success_rate == pytest.approx(2 / 3)


def test_run_observer_calculates_failure_rate() -> None:
    observer = RunObserver()

    observation = observer.observe(
        outcome=make_outcome(
            status=ResearchRunStatus.PARTIAL,
            completed_tasks=2,
            failed_tasks=1,
        ),
        duration_seconds=3.0,
    )

    assert observation.failure_rate == pytest.approx(1 / 3)


def test_run_observer_handles_zero_tasks() -> None:
    observer = RunObserver()

    observation = observer.observe(
        outcome=make_outcome(
            status=ResearchRunStatus.SUCCESS,
            completed_tasks=0,
            failed_tasks=0,
        ),
        duration_seconds=0.0,
    )

    assert observation.total_tasks == 0
    assert observation.success_rate == 0.0
    assert observation.failure_rate == 0.0


def test_run_observer_rejects_negative_duration() -> None:
    observer = RunObserver()

    with pytest.raises(
        ValueError,
        match="duration_seconds must not be negative",
    ):
        observer.observe(
            outcome=make_outcome(
                status=ResearchRunStatus.SUCCESS,
                completed_tasks=1,
                failed_tasks=0,
            ),
            duration_seconds=-0.1,
        )
