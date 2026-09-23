from datetime import UTC, datetime, timedelta

import pytest

from app.application.tracing.recorder import TraceRecorder
from app.domain.tracing.models import TraceEventStatus, TraceEventType
from app.infrastructure.tracing.tracing_llm_provider import TracingLLMProvider
from app.infrastructure.tracing.tracing_search_provider import TracingSearchProvider


class StepClock:
    def __init__(self, start: datetime, step_seconds: float = 1.0) -> None:
        self._current = start
        self._step = timedelta(seconds=step_seconds)

    def now(self) -> datetime:
        value = self._current
        self._current += self._step
        return value


class StubSearchProvider:
    def __init__(self, results=None, exc: Exception | None = None) -> None:
        self.results = results or []
        self.exc = exc
        self.calls: list[str] = []

    def search(self, query: str):
        self.calls.append(query)

        if self.exc:
            raise self.exc

        return self.results


class StubLLMProvider:
    def __init__(self, output=None, exc: Exception | None = None) -> None:
        self.output = output or [{"answer": "ok"}]
        self.exc = exc
        self.prompts: list[str] = []

    def generate(self, prompt: str):
        self.prompts.append(prompt)

        if self.exc:
            raise self.exc

        return self.output


def new_recorder() -> TraceRecorder:
    return TraceRecorder(
        "Research reliability",
        clock=StepClock(datetime(2026, 9, 23, tzinfo=UTC)),
    )


def test_tracing_search_provider_passes_results_through_unchanged() -> None:
    stub = StubSearchProvider(results=[{"title": "A"}])
    recorder = new_recorder()
    provider = TracingSearchProvider(stub, recorder)

    results = provider.search("CAP theorem")

    assert results == [{"title": "A"}]


def test_tracing_search_provider_records_a_successful_tool_call() -> None:
    stub = StubSearchProvider(results=[{"title": "A"}, {"title": "B"}])
    recorder = new_recorder()
    provider = TracingSearchProvider(stub, recorder)

    provider.search("CAP theorem")
    run = recorder.finish(final_answer="An answer.")

    assert len(run.events) == 1
    event = run.events[0]

    assert event.event_type == TraceEventType.TOOL_CALL
    assert event.status == TraceEventStatus.SUCCESS
    assert event.tool_call.tool_name == "search"
    assert event.tool_call.arguments == {"query": "CAP theorem"}
    assert "2 result" in event.tool_call.result_summary


def test_tracing_search_provider_records_a_failed_tool_call_and_reraises() -> None:
    stub = StubSearchProvider(exc=ConnectionError("timed out"))
    recorder = new_recorder()
    provider = TracingSearchProvider(stub, recorder)

    with pytest.raises(ConnectionError, match="timed out"):
        provider.search("CAP theorem")

    run = recorder.finish(error="retrieval failed")

    assert len(run.events) == 1
    assert run.events[0].status == TraceEventStatus.FAILED
    assert "ConnectionError" in run.events[0].tool_call.error


def test_tracing_llm_provider_records_a_successful_model_call() -> None:
    stub = StubLLMProvider(output=[{"summary": "..."}])
    recorder = new_recorder()
    provider = TracingLLMProvider(
        stub, provider_name="openai", model="gpt-5-mini", recorder=recorder
    )

    provider.generate("Analyze this evidence.")
    run = recorder.finish(final_answer="An answer.")

    assert len(run.events) == 1
    event = run.events[0]

    assert event.event_type == TraceEventType.MODEL_CALL
    assert event.status == TraceEventStatus.SUCCESS
    assert event.model_call.provider == "openai"
    assert event.model_call.model == "gpt-5-mini"
    assert "Analyze" in event.model_call.prompt_summary


def test_tracing_llm_provider_records_a_failed_model_call_and_reraises() -> None:
    stub = StubLLMProvider(exc=ValueError("invalid JSON"))
    recorder = new_recorder()
    provider = TracingLLMProvider(stub, provider_name="openai", recorder=recorder)

    with pytest.raises(ValueError, match="invalid JSON"):
        provider.generate("Analyze this evidence.")

    run = recorder.finish(error="analysis failed")

    assert run.events[0].status == TraceEventStatus.FAILED
    assert "ValueError" in run.events[0].model_call.error


def test_tracing_llm_provider_truncates_long_prompts_and_outputs() -> None:
    long_prompt = "x" * 5000
    stub = StubLLMProvider(output=[{"answer": "y" * 5000}])
    recorder = new_recorder()
    provider = TracingLLMProvider(stub, provider_name="openai", recorder=recorder)

    provider.generate(long_prompt)
    run = recorder.finish(final_answer="An answer.")

    call = run.events[0].model_call

    assert len(call.prompt_summary) < 5000
    assert len(call.output_summary) < 5000
    assert "chars total" in call.prompt_summary


def test_multiple_calls_are_recorded_in_call_order() -> None:
    """Ordering across two different wrapped providers sharing one recorder."""
    recorder = new_recorder()
    search = TracingSearchProvider(StubSearchProvider(results=[]), recorder)
    llm = TracingLLMProvider(
        StubLLMProvider(), provider_name="openai", recorder=recorder
    )

    search.search("first")
    llm.generate("second")
    search.search("third")

    run = recorder.finish(final_answer="done")

    labels = [
        (event.sequence, event.event_type.value, event.tool_call.arguments["query"])
        if event.tool_call
        else (event.sequence, event.event_type.value, None)
        for event in run.events
    ]

    assert labels == [
        (0, "tool_call", "first"),
        (1, "model_call", None),
        (2, "tool_call", "third"),
    ]
