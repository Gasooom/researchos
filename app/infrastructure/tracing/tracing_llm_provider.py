"""LLM provider decorator that records model calls."""

from app.application.tracing.recorder import Clock, SystemClock, TraceRecorder
from app.domain.tracing.models import ModelCall, TraceEventStatus

PROMPT_SUMMARY_LENGTH = 200
OUTPUT_SUMMARY_LENGTH = 200


def _summarize(value: str, limit: int) -> str:
    """Truncate long text for a trace summary rather than storing it whole."""
    stripped = value.strip()

    if len(stripped) <= limit:
        return stripped

    return f"{stripped[:limit]}... ({len(stripped)} chars total)"


class TracingLLMProvider:
    """Wrap an LLMProvider and record each call as a ModelCall event.

    Implements the same generate(prompt) -> list[dict] contract as the wrapped
    instance, so it is a drop-in replacement wherever an LLMProvider is
    expected. Prompts and outputs are stored as bounded summaries, not in
    full, to keep traces small.
    """

    def __init__(
        self,
        provider,
        provider_name: str,
        recorder: TraceRecorder,
        model: str | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.provider = provider
        self.provider_name = provider_name
        self.model = model
        self.recorder = recorder
        self.clock = clock or SystemClock()

    def generate(self, prompt: str) -> list[dict[str, object]]:
        """Generate, recording the call as a trace event regardless of outcome."""
        started_at = self.clock.now()

        try:
            results = self.provider.generate(prompt)
        except Exception as exc:
            completed_at = self.clock.now()

            self.recorder.record_model_call(
                label="generate",
                started_at=started_at,
                completed_at=completed_at,
                model_call=ModelCall(
                    provider=self.provider_name,
                    model=self.model,
                    prompt_summary=_summarize(prompt, PROMPT_SUMMARY_LENGTH),
                    output_summary="no output: call raised an exception",
                    status=TraceEventStatus.FAILED,
                    error=f"{type(exc).__name__}: {exc}",
                ),
            )

            raise

        completed_at = self.clock.now()

        self.recorder.record_model_call(
            label="generate",
            started_at=started_at,
            completed_at=completed_at,
            model_call=ModelCall(
                provider=self.provider_name,
                model=self.model,
                prompt_summary=_summarize(prompt, PROMPT_SUMMARY_LENGTH),
                output_summary=_summarize(str(results), OUTPUT_SUMMARY_LENGTH),
                status=TraceEventStatus.SUCCESS,
            ),
        )

        return results
