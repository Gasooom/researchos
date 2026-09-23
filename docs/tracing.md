# Agent run tracing

A trace answers: what did the pipeline do, which tools and models did it
call, in what order, with what arguments, what came back, where did it fail,
how long did each step take, and what was the final answer.

## What "agent" means here, stated plainly

ResearchOS's "agents" (`RetrievalAgent`, `AnalysisAgent`, `SynthesisAgent`)
are fixed, role-specialized pipeline stages. `MultiAgentCoordinator` always
runs retrieval, then analysis, then synthesis, in that order, for every task
— nothing decides to skip a stage, retry with a different tool, or loop.
There is no autonomous tool-selection.

An `AgentRun` is one execution of that fixed pipeline for one research task.
The name reflects the codebase's own terminology for these components, not a
claim that the system exhibits autonomous agent behavior. If you're looking
for a ReAct-style loop, this isn't it — and this document says so rather than
implying otherwise.

## Model

```
AgentRun
  ├── id, task_objective, status, started_at, completed_at, final_answer
  └── events: [TraceEvent]        # ordered by sequence, 0-indexed
        ├── event_type: tool_call | model_call | final_answer | error
        ├── status: success | failed
        ├── started_at, completed_at  → duration_seconds
        ├── tool_call: ToolCall        (only on tool_call events)
        │     tool_name, arguments, result_summary, status, error
        └── model_call: ModelCall      (only on model_call events)
              provider, model, prompt_summary, output_summary, status, error
```

`AgentRun.status` reuses the existing `ResearchRunStatus` enum
(`success` / `partial` / `failed`) for consistency with `ResearchRunOutcome`
elsewhere in the codebase. `partial` means at least one event failed but a
final answer was still produced.

Every `TraceEvent.run_id` must equal its parent `AgentRun.id`, and events
must be stored in ascending `sequence` order — both enforced by a Pydantic
validator, not just convention. Prompts and outputs are stored as bounded
summaries (`prompt_summary`, `output_summary`), not in full, to keep traces a
reasonable size; full content isn't needed to answer the "what did it do"
questions above.

Files: `app/domain/tracing/models.py`.

## Capturing a trace

`TraceRecorder` (`app/application/tracing/recorder.py`) accumulates events
for one run and assembles the `AgentRun` when `finish()` is called:

```python
from app.application.tracing.recorder import TraceRecorder

recorder = TraceRecorder(task.objective)
# ... wrap providers with the recorder, run the pipeline ...
run = recorder.finish(final_answer=result.synthesis.answer)
```

Capture is transparent: `TracingSearchProvider` and `TracingLLMProvider`
(`app/infrastructure/tracing/`) implement the exact same `SearchProvider` and
`LLMProvider` contracts the real adapters do, so they're drop-in substitutes.
**No agent, coordinator, or orchestrator code changes to be traced** — wrap
the provider passed into `RetrievalAgent` / `LLMAnalysisAgent` /
`LLMSynthesisAgent` instead of the agent itself:

```python
from app.application.tracing.recorder import TraceRecorder
from app.infrastructure.tracing.tracing_search_provider import TracingSearchProvider
from app.infrastructure.tracing.tracing_llm_provider import TracingLLMProvider

recorder = TraceRecorder(task.objective)

retrieval_agent = RetrievalAgent(
    search_provider=TracingSearchProvider(real_search_provider, recorder),
)
analysis_agent = LLMAnalysisAgent(
    provider=TracingLLMProvider(
        real_llm_provider, "openai", recorder, model="gpt-5-mini"
    ),
)
```

An exception from the wrapped provider is recorded as a failed event with
its type and message, then re-raised unchanged — tracing observes, it never
swallows or alters pipeline behavior. Every existing test in
`tests/integration/orchestration/` and `tests/e2e/` passes untouched, because
nothing about `ResearchOrchestrator`, `MultiAgentCoordinator`, or
`bootstrap/container.py` was modified.

## Persistence

`AgentRunRepository` (`app/domain/tracing/repository.py`) is a `Protocol`
mirroring the existing `ResearchRunRepository` pattern, with an in-memory
implementation (`InMemoryAgentRunRepository`) for tests and lightweight use.

## Scope: not wired into production

This milestone deliberately stops short of wiring tracing into
`bootstrap/container.py` or exposing it through the API. Two reasons:

1. `ResearchOrchestrator` runs three tasks per request through
   `MultiAgentCoordinator`; capturing all three as a coherent trace, and
   deciding how (or whether) to persist that alongside `ResearchRunRecord`,
   is a design decision that deserves its own scoped change rather than being
   folded into "add the trace model."
2. The current `SQLiteResearchRunRepository` has no trace column, and adding
   one is a schema change with its own testing surface.

Wiring this into the live pipeline — likely by having `ResearchOrchestrator`
construct one `TraceRecorder` per task, wrap that task's providers, and
attach the resulting `AgentRun` list to `ResearchRunRecord` — is a natural
next step, not attempted here.

## Tests

- `tests/unit/tracing/test_trace_models.py` — validation (invalid traces:
  missing payload, mismatched event type, out-of-order sequence, cross-run
  correlation, backwards timestamps), valid construction, JSON round-trip.
- `tests/unit/tracing/test_trace_recorder.py` — sequencing, run-id
  correlation, status derivation (success / partial / failed).
- `tests/unit/tracing/test_tracing_providers.py` — tool and model calls
  captured on success and failure, prompt/output truncation, cross-provider
  ordering.
- `tests/integration/tracing/test_agent_run_capture.py` — the real
  `RetrievalAgent` + `LLMAnalysisAgent` + `LLMSynthesisAgent` +
  `MultiAgentCoordinator` stack, traced end to end: verifies what ran, in
  what order, with what arguments, what came back, the final answer, timing,
  a failure path, and persistence round-trip.
