from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.runs.models import ResearchRunStatus
from app.domain.tracing.models import (
    AgentRun,
    ModelCall,
    ToolCall,
    TraceEvent,
    TraceEventStatus,
    TraceEventType,
)

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)


def make_tool_call_event(run_id, sequence=0, status=TraceEventStatus.SUCCESS):
    return TraceEvent(
        run_id=run_id,
        sequence=sequence,
        event_type=TraceEventType.TOOL_CALL,
        label="search",
        started_at=NOW,
        completed_at=NOW + timedelta(seconds=2),
        status=status,
        tool_call=ToolCall(
            tool_name="search",
            arguments={"query": "CAP theorem"},
            result_summary="5 results",
            status=status,
        ),
    )


def test_tool_call_event_requires_a_tool_call_payload() -> None:
    with pytest.raises(ValidationError, match="tool_call event must carry"):
        TraceEvent(
            run_id=uuid4(),
            sequence=0,
            event_type=TraceEventType.TOOL_CALL,
            label="search",
            started_at=NOW,
            completed_at=NOW,
            status=TraceEventStatus.SUCCESS,
        )


def test_model_call_event_requires_a_model_call_payload() -> None:
    with pytest.raises(ValidationError, match="model_call event must carry"):
        TraceEvent(
            run_id=uuid4(),
            sequence=0,
            event_type=TraceEventType.MODEL_CALL,
            label="generate",
            started_at=NOW,
            completed_at=NOW,
            status=TraceEventStatus.SUCCESS,
        )


def test_final_answer_event_must_not_carry_a_tool_call() -> None:
    with pytest.raises(ValidationError, match="must not carry"):
        TraceEvent(
            run_id=uuid4(),
            sequence=0,
            event_type=TraceEventType.FINAL_ANSWER,
            label="final answer",
            started_at=NOW,
            completed_at=NOW,
            status=TraceEventStatus.SUCCESS,
            tool_call=ToolCall(
                tool_name="search",
                arguments={},
                result_summary="n/a",
                status=TraceEventStatus.SUCCESS,
            ),
        )


def test_event_completed_at_must_not_precede_started_at() -> None:
    with pytest.raises(ValidationError, match="must not precede"):
        TraceEvent(
            run_id=uuid4(),
            sequence=0,
            event_type=TraceEventType.FINAL_ANSWER,
            label="final answer",
            started_at=NOW,
            completed_at=NOW - timedelta(seconds=1),
            status=TraceEventStatus.SUCCESS,
        )


def test_valid_tool_call_event_computes_duration() -> None:
    event = make_tool_call_event(run_id=uuid4())

    assert event.duration_seconds == pytest.approx(2.0)


def test_agent_run_rejects_events_from_another_run() -> None:
    run_id = uuid4()
    other_run_event = make_tool_call_event(run_id=uuid4())

    with pytest.raises(ValidationError, match="expected"):
        AgentRun(
            id=run_id,
            task_objective="Research reliability",
            status=ResearchRunStatus.SUCCESS,
            started_at=NOW,
            completed_at=NOW + timedelta(seconds=5),
            events=[other_run_event],
        )


def test_agent_run_rejects_out_of_order_sequences() -> None:
    run_id = uuid4()
    events = [
        make_tool_call_event(run_id, sequence=1),
        make_tool_call_event(run_id, sequence=0),
    ]

    with pytest.raises(ValidationError, match="ascending sequence"):
        AgentRun(
            id=run_id,
            task_objective="Research reliability",
            status=ResearchRunStatus.SUCCESS,
            started_at=NOW,
            completed_at=NOW + timedelta(seconds=5),
            events=events,
        )


def test_valid_agent_run_exposes_tool_and_model_calls() -> None:
    run_id = uuid4()

    tool_event = make_tool_call_event(run_id, sequence=0)
    model_event = TraceEvent(
        run_id=run_id,
        sequence=1,
        event_type=TraceEventType.MODEL_CALL,
        label="generate",
        started_at=NOW + timedelta(seconds=2),
        completed_at=NOW + timedelta(seconds=6),
        status=TraceEventStatus.SUCCESS,
        model_call=ModelCall(
            provider="openai",
            model="gpt-5-mini",
            prompt_summary="Analyze evidence...",
            output_summary='{"summary": "..."}',
            status=TraceEventStatus.SUCCESS,
        ),
    )

    run = AgentRun(
        id=run_id,
        task_objective="Research reliability",
        status=ResearchRunStatus.SUCCESS,
        started_at=NOW,
        completed_at=NOW + timedelta(seconds=6),
        events=[tool_event, model_event],
        final_answer="Reliability improves with evaluation.",
    )

    assert len(run.tool_calls) == 1
    assert len(run.model_calls) == 1
    assert run.tool_calls[0].tool_name == "search"
    assert run.model_calls[0].provider == "openai"
    assert run.duration_seconds == pytest.approx(6.0)
    assert run.failed_events == []


def test_agent_run_surfaces_failed_events() -> None:
    run_id = uuid4()
    failed_event = make_tool_call_event(
        run_id,
        sequence=0,
        status=TraceEventStatus.FAILED,
    )

    run = AgentRun(
        id=run_id,
        task_objective="Research reliability",
        status=ResearchRunStatus.FAILED,
        started_at=NOW,
        completed_at=NOW + timedelta(seconds=2),
        events=[failed_event],
    )

    assert len(run.failed_events) == 1
    assert run.failed_events[0].status == TraceEventStatus.FAILED


def test_agent_run_round_trips_through_json() -> None:
    """Serialization/deserialization preserves structure and ordering."""
    run_id = uuid4()
    events = [make_tool_call_event(run_id, sequence=i) for i in range(3)]

    run = AgentRun(
        id=run_id,
        task_objective="Research reliability",
        status=ResearchRunStatus.SUCCESS,
        started_at=NOW,
        completed_at=NOW + timedelta(seconds=6),
        events=events,
        final_answer="Reliability improves with evaluation.",
    )

    restored = AgentRun.model_validate_json(run.model_dump_json())

    assert restored == run
    assert [event.sequence for event in restored.events] == [0, 1, 2]
