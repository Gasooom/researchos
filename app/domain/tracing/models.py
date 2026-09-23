"""Trace domain models for ResearchOS.

Naming note, stated up front rather than left implicit: this codebase's
"agents" (RetrievalAgent, AnalysisAgent, SynthesisAgent) are fixed,
role-specialized pipeline stages, not autonomous agents that decide which
tool to call next. MultiAgentCoordinator always runs retrieval, then
analysis, then synthesis, in that order, for every task. An `AgentRun`
here means one execution of that fixed pipeline for one research task -
not an autonomous tool-selecting loop. Calling it an "agent run" reflects
the codebase's own terminology for these components, not a claim that the
system exhibits autonomous agent behavior.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from app.domain.runs.models import ResearchRunStatus


class TraceEventType(StrEnum):
    """The kind of step a trace event records."""

    TOOL_CALL = "tool_call"
    MODEL_CALL = "model_call"
    FINAL_ANSWER = "final_answer"
    ERROR = "error"


class TraceEventStatus(StrEnum):
    """Outcome of a single trace event."""

    SUCCESS = "success"
    FAILED = "failed"


class ToolCall(BaseModel):
    """A single call to an external tool (e.g. a search provider)."""

    tool_name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)
    result_summary: str = Field(min_length=1)
    status: TraceEventStatus
    error: str | None = None


class ModelCall(BaseModel):
    """A single call to an LLM provider."""

    provider: str = Field(min_length=1)
    model: str | None = None
    prompt_summary: str = Field(min_length=1)
    output_summary: str = Field(min_length=1)
    status: TraceEventStatus
    error: str | None = None


class TraceEvent(BaseModel):
    """One ordered step within an agent run."""

    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    sequence: int = Field(ge=0)
    event_type: TraceEventType
    label: str = Field(min_length=1)
    started_at: datetime
    completed_at: datetime
    status: TraceEventStatus
    tool_call: ToolCall | None = None
    model_call: ModelCall | None = None
    error: str | None = None

    @property
    def duration_seconds(self) -> float:
        """Return how long this step took."""
        return (self.completed_at - self.started_at).total_seconds()

    @model_validator(mode="after")
    def _check_payload_matches_type(self) -> "TraceEvent":
        """Require the detail payload to match the declared event type."""
        if self.event_type == TraceEventType.TOOL_CALL and self.tool_call is None:
            raise ValueError("a tool_call event must carry a ToolCall")

        if self.event_type == TraceEventType.MODEL_CALL and self.model_call is None:
            raise ValueError("a model_call event must carry a ModelCall")

        if self.event_type in (TraceEventType.FINAL_ANSWER, TraceEventType.ERROR):
            if self.tool_call is not None or self.model_call is not None:
                raise ValueError(
                    f"a {self.event_type.value} event must not carry a "
                    "tool_call or model_call"
                )

        if self.completed_at < self.started_at:
            raise ValueError("completed_at must not precede started_at")

        return self


class AgentRun(BaseModel):
    """One captured execution of the fixed retrieval/analysis/synthesis pipeline."""

    id: UUID = Field(default_factory=uuid4)
    task_objective: str = Field(min_length=1)
    status: ResearchRunStatus
    started_at: datetime
    completed_at: datetime
    events: list[TraceEvent] = Field(default_factory=list)
    final_answer: str | None = None
    error: str | None = None

    @property
    def duration_seconds(self) -> float:
        """Return the total wall-clock duration of the run."""
        return (self.completed_at - self.started_at).total_seconds()

    @property
    def tool_calls(self) -> list[ToolCall]:
        """Return every tool call made during this run, in order."""
        return [event.tool_call for event in self.events if event.tool_call]

    @property
    def model_calls(self) -> list[ModelCall]:
        """Return every model call made during this run, in order."""
        return [event.model_call for event in self.events if event.model_call]

    @property
    def failed_events(self) -> list[TraceEvent]:
        """Return events that did not succeed."""
        return [
            event for event in self.events if event.status == TraceEventStatus.FAILED
        ]

    @model_validator(mode="after")
    def _check_events_belong_to_this_run(self) -> "AgentRun":
        """Require every event to be correlated to this run."""
        for event in self.events:
            if event.run_id != self.id:
                raise ValueError(
                    f"event {event.id} has run_id {event.run_id}, expected {self.id}"
                )

        sequences = [event.sequence for event in self.events]

        if sequences != sorted(sequences):
            raise ValueError("events must be ordered by ascending sequence")

        return self
