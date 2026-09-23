"""Trace capture service for ResearchOS."""

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from app.domain.runs.models import ResearchRunStatus
from app.domain.tracing.models import (
    AgentRun,
    ModelCall,
    ToolCall,
    TraceEvent,
    TraceEventStatus,
    TraceEventType,
)


class Clock(Protocol):
    """Protocol for obtaining the current timestamp."""

    def now(self) -> datetime:
        """Return the current timezone-aware timestamp."""
        ...


class SystemClock:
    """Production clock using the current UTC time."""

    def now(self) -> datetime:
        """Return the current UTC timestamp."""
        return datetime.now(UTC)


class TraceRecorder:
    """Accumulate trace events for one agent run and assemble the result.

    A recorder is scoped to a single run: construct one per
    MultiAgentCoordinator.execute(task) invocation, pass its tool_call/
    model_call methods (or a wrapper built around them) down to the
    providers involved, then call finish() once the run completes.
    """

    def __init__(
        self,
        task_objective: str,
        clock: Clock | None = None,
        run_id: UUID | None = None,
    ) -> None:
        self.id = run_id or uuid4()
        self.task_objective = task_objective
        self.clock = clock or SystemClock()
        self._events: list[TraceEvent] = []
        self._next_sequence = 0
        self._started_at = self.clock.now()

    def record_tool_call(
        self,
        label: str,
        started_at: datetime,
        completed_at: datetime,
        tool_call: ToolCall,
    ) -> TraceEvent:
        """Record a completed tool call."""
        return self._record(
            event_type=TraceEventType.TOOL_CALL,
            label=label,
            started_at=started_at,
            completed_at=completed_at,
            status=tool_call.status,
            tool_call=tool_call,
            error=tool_call.error,
        )

    def record_model_call(
        self,
        label: str,
        started_at: datetime,
        completed_at: datetime,
        model_call: ModelCall,
    ) -> TraceEvent:
        """Record a completed model call."""
        return self._record(
            event_type=TraceEventType.MODEL_CALL,
            label=label,
            started_at=started_at,
            completed_at=completed_at,
            status=model_call.status,
            model_call=model_call,
            error=model_call.error,
        )

    def record_error(self, label: str, error: str) -> TraceEvent:
        """Record a run-level failure not tied to one tool or model call."""
        now = self.clock.now()

        return self._record(
            event_type=TraceEventType.ERROR,
            label=label,
            started_at=now,
            completed_at=now,
            status=TraceEventStatus.FAILED,
            error=error,
        )

    def _record(
        self,
        event_type: TraceEventType,
        label: str,
        started_at: datetime,
        completed_at: datetime,
        status: TraceEventStatus,
        tool_call: ToolCall | None = None,
        model_call: ModelCall | None = None,
        error: str | None = None,
    ) -> TraceEvent:
        event = TraceEvent(
            run_id=self.id,
            sequence=self._next_sequence,
            event_type=event_type,
            label=label,
            started_at=started_at,
            completed_at=completed_at,
            status=status,
            tool_call=tool_call,
            model_call=model_call,
            error=error,
        )

        self._next_sequence += 1
        self._events.append(event)

        return event

    def finish(
        self,
        final_answer: str | None = None,
        error: str | None = None,
    ) -> AgentRun:
        """Assemble the completed agent run from recorded events."""
        completed_at = self.clock.now()

        if error is not None:
            status = ResearchRunStatus.FAILED
        elif any(event.status == TraceEventStatus.FAILED for event in self._events):
            status = (
                ResearchRunStatus.PARTIAL
                if final_answer is not None
                else ResearchRunStatus.FAILED
            )
        else:
            status = ResearchRunStatus.SUCCESS

        return AgentRun(
            id=self.id,
            task_objective=self.task_objective,
            status=status,
            started_at=self._started_at,
            completed_at=completed_at,
            events=list(self._events),
            final_answer=final_answer,
            error=error,
        )
