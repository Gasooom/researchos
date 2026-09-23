"""End-to-end proof that a real pipeline execution can be captured as a trace.

Uses the actual RetrievalAgent, LLMAnalysisAgent, LLMSynthesisAgent, and
MultiAgentCoordinator classes ResearchOrchestrator uses in production, with
tracing wrappers substituted for the search and LLM providers. No production
code (ResearchOrchestrator, bootstrap/container.py) is modified for this.
"""

import json

from app.application.agents.llm_analysis import LLMAnalysisAgent
from app.application.agents.llm_synthesis import LLMSynthesisAgent
from app.application.agents.retrieval import RetrievalAgent
from app.application.orchestration.multi_agent import MultiAgentCoordinator
from app.application.tracing.recorder import TraceRecorder
from app.domain.research.models import ResearchTask
from app.domain.runs.models import ResearchRunStatus
from app.domain.tracing.models import TraceEventType
from app.infrastructure.persistence.in_memory_agent_run_repository import (
    InMemoryAgentRunRepository,
)
from app.infrastructure.tracing.tracing_llm_provider import TracingLLMProvider
from app.infrastructure.tracing.tracing_search_provider import TracingSearchProvider


class StubSearchProvider:
    """Deterministic search results for the traced integration test."""

    def search(self, query: str) -> list[dict[str, str | float]]:
        return [
            {
                "title": "AI Agent Reliability",
                "url": "https://example.com/reliability",
                "publisher": "Example Research",
                "excerpt": "AI agents can fail unpredictably without evaluation.",
                "relevance": 0.94,
            },
        ]


class StubLLMProvider:
    """Deterministic LLM output for the traced integration test.

    Returns a different structured response depending on whether it is being
    asked to analyze evidence or synthesize a final answer, matching what
    LLMAnalysisAgent and LLMSynthesisAgent each expect back.
    """

    def generate(self, prompt: str) -> list[dict[str, object]]:
        if "synthesis specialist" in prompt:
            return [
                {
                    "answer": "Evaluation improves agent reliability.",
                    "supporting_points": ["Evaluation catches unpredictable failures."],
                    "confidence": 0.9,
                }
            ]

        return [
            {
                "summary": "Evidence indicates evaluation reduces failure risk.",
                "key_points": ["Agents fail unpredictably without evaluation."],
                "confidence": 0.9,
            }
        ]


def build_traced_coordinator(recorder: TraceRecorder) -> MultiAgentCoordinator:
    """Build the real multi-agent pipeline with tracing wrappers substituted in."""
    search_provider = TracingSearchProvider(StubSearchProvider(), recorder)
    llm_provider = TracingLLMProvider(
        StubLLMProvider(),
        provider_name="openai",
        model="gpt-5-mini",
        recorder=recorder,
    )

    return MultiAgentCoordinator(
        retrieval_agent=RetrievalAgent(search_provider=search_provider),
        analysis_agent=LLMAnalysisAgent(provider=llm_provider),
        synthesis_agent=LLMSynthesisAgent(provider=llm_provider),
    )


def test_a_real_pipeline_execution_is_captured_end_to_end() -> None:
    task = ResearchTask(
        objective="Investigate AI agent reliability.",
        task_type="research",
        max_sources=3,
    )

    recorder = TraceRecorder(task.objective)
    coordinator = build_traced_coordinator(recorder)

    result = coordinator.execute(task)
    run = recorder.finish(final_answer=result.synthesis.answer)

    # What did it do, and in what order?
    assert [event.event_type for event in run.events] == [
        TraceEventType.TOOL_CALL,
        TraceEventType.MODEL_CALL,
        TraceEventType.MODEL_CALL,
    ]

    # Which tool did it call, with what arguments, and what came back?
    tool_call = run.tool_calls[0]
    assert tool_call.tool_name == "search"
    assert tool_call.arguments == {"query": task.objective}
    assert "1 result" in tool_call.result_summary

    # Which model calls happened, and what was sent/returned?
    assert len(run.model_calls) == 2
    assert all(call.provider == "openai" for call in run.model_calls)
    assert all(call.model == "gpt-5-mini" for call in run.model_calls)

    # What was the final answer, and did the run succeed?
    assert run.final_answer == "Evaluation improves agent reliability."
    assert run.status == ResearchRunStatus.SUCCESS
    assert run.failed_events == []

    # How long did each step take?
    assert all(event.duration_seconds >= 0 for event in run.events)
    assert run.duration_seconds >= 0

    # Can it be persisted and retrieved?
    repository = InMemoryAgentRunRepository()
    repository.save(run)

    stored = repository.get(run.id)
    assert stored == run
    assert stored in repository.list()


def test_a_failing_tool_call_is_captured_as_a_failed_run() -> None:
    class FailingSearchProvider:
        def search(self, query: str) -> list[dict[str, str | float]]:
            raise ConnectionError("search backend unreachable")

    task = ResearchTask(
        objective="Investigate AI agent reliability.",
        task_type="research",
        max_sources=3,
    )

    recorder = TraceRecorder(task.objective)
    search_provider = TracingSearchProvider(FailingSearchProvider(), recorder)
    retrieval_agent = RetrievalAgent(search_provider=search_provider)

    error_message = None

    try:
        retrieval_agent.execute(task)
    except ConnectionError as exc:
        error_message = str(exc)

    run = recorder.finish(error=f"retrieval failed: {error_message}")

    assert run.status == ResearchRunStatus.FAILED
    assert len(run.failed_events) == 1
    assert run.failed_events[0].event_type == TraceEventType.TOOL_CALL
    assert "unreachable" in run.failed_events[0].tool_call.error


def test_captured_run_serializes_to_json_for_external_inspection() -> None:
    """A trace should be inspectable outside the process, e.g. by an API or CLI."""
    task = ResearchTask(
        objective="Investigate AI agent reliability.",
        task_type="research",
        max_sources=3,
    )

    recorder = TraceRecorder(task.objective)
    coordinator = build_traced_coordinator(recorder)
    result = coordinator.execute(task)
    run = recorder.finish(final_answer=result.synthesis.answer)

    payload = json.loads(run.model_dump_json())

    assert payload["task_objective"] == task.objective
    assert payload["status"] == "success"
    assert len(payload["events"]) == 3
    assert payload["events"][0]["event_type"] == "tool_call"
