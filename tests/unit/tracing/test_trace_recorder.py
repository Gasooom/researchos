from datetime import UTC, datetime, timedelta

from app.application.tracing.recorder import TraceRecorder
from app.domain.runs.models import ResearchRunStatus
from app.domain.tracing.models import ModelCall, ToolCall, TraceEventStatus


class StepClock:
    """Deterministic clock advancing by a fixed step on every call."""

    def __init__(self, start: datetime, step_seconds: float = 1.0) -> None:
        self._current = start
        self._step = timedelta(seconds=step_seconds)

    def now(self) -> datetime:
        value = self._current
        self._current += self._step
        return value


def make_tool_call(status: TraceEventStatus = TraceEventStatus.SUCCESS) -> ToolCall:
    return ToolCall(
        tool_name="search",
        arguments={"query": "CAP theorem"},
        result_summary="5 results",
        status=status,
    )


def make_model_call(status: TraceEventStatus = TraceEventStatus.SUCCESS) -> ModelCall:
    return ModelCall(
        provider="openai",
        model="gpt-5-mini",
        prompt_summary="Analyze...",
        output_summary="{}",
        status=status,
    )


def test_recorder_assigns_ascending_sequence_numbers() -> None:
    clock = StepClock(datetime(2026, 9, 23, tzinfo=UTC))
    recorder = TraceRecorder("Research reliability", clock=clock)

    recorder.record_tool_call("search", clock.now(), clock.now(), make_tool_call())
    recorder.record_model_call("generate", clock.now(), clock.now(), make_model_call())

    run = recorder.finish(final_answer="An answer.")

    assert [event.sequence for event in run.events] == [0, 1]
    assert [event.event_type.value for event in run.events] == [
        "tool_call",
        "model_call",
    ]


def test_recorder_stamps_every_event_with_the_run_id() -> None:
    recorder = TraceRecorder(
        "Research reliability",
        clock=StepClock(datetime(2026, 9, 23, tzinfo=UTC)),
    )

    recorder.record_tool_call(
        "search",
        datetime(2026, 9, 23, tzinfo=UTC),
        datetime(2026, 9, 23, 0, 0, 2, tzinfo=UTC),
        make_tool_call(),
    )

    run = recorder.finish()

    assert all(event.run_id == run.id for event in run.events)


def test_recorder_reports_success_when_all_events_succeed() -> None:
    recorder = TraceRecorder(
        "Research reliability",
        clock=StepClock(datetime(2026, 9, 23, tzinfo=UTC)),
    )

    recorder.record_tool_call(
        "search",
        datetime(2026, 9, 23, tzinfo=UTC),
        datetime(2026, 9, 23, 0, 0, 2, tzinfo=UTC),
        make_tool_call(),
    )

    run = recorder.finish(final_answer="An answer.")

    assert run.status == ResearchRunStatus.SUCCESS


def test_recorder_reports_partial_when_some_events_fail_but_answer_exists() -> None:
    recorder = TraceRecorder(
        "Research reliability",
        clock=StepClock(datetime(2026, 9, 23, tzinfo=UTC)),
    )

    recorder.record_tool_call(
        "search",
        datetime(2026, 9, 23, tzinfo=UTC),
        datetime(2026, 9, 23, 0, 0, 2, tzinfo=UTC),
        make_tool_call(status=TraceEventStatus.FAILED),
    )

    run = recorder.finish(final_answer="A partial answer.")

    assert run.status == ResearchRunStatus.PARTIAL


def test_recorder_reports_failed_when_no_answer_and_a_failure_exists() -> None:
    recorder = TraceRecorder(
        "Research reliability",
        clock=StepClock(datetime(2026, 9, 23, tzinfo=UTC)),
    )

    recorder.record_tool_call(
        "search",
        datetime(2026, 9, 23, tzinfo=UTC),
        datetime(2026, 9, 23, 0, 0, 2, tzinfo=UTC),
        make_tool_call(status=TraceEventStatus.FAILED),
    )

    run = recorder.finish(final_answer=None)

    assert run.status == ResearchRunStatus.FAILED


def test_recorder_reports_failed_when_an_explicit_error_is_given() -> None:
    recorder = TraceRecorder(
        "Research reliability",
        clock=StepClock(datetime(2026, 9, 23, tzinfo=UTC)),
    )

    run = recorder.finish(error="no evidence was retrieved")

    assert run.status == ResearchRunStatus.FAILED
    assert run.error == "no evidence was retrieved"


def test_record_error_appends_a_failed_error_event() -> None:
    recorder = TraceRecorder(
        "Research reliability",
        clock=StepClock(datetime(2026, 9, 23, tzinfo=UTC)),
    )

    recorder.record_error("planning", "no tasks were generated")
    run = recorder.finish(error="no tasks were generated")

    assert len(run.events) == 1
    assert run.events[0].event_type.value == "error"
    assert run.events[0].status == TraceEventStatus.FAILED


def test_recorder_preserves_task_objective_on_the_finished_run() -> None:
    recorder = TraceRecorder(
        "Investigate AI agent reliability",
        clock=StepClock(datetime(2026, 9, 23, tzinfo=UTC)),
    )

    run = recorder.finish(final_answer="An answer.")

    assert run.task_objective == "Investigate AI agent reliability"
