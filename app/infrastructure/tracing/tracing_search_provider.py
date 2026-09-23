"""Search provider decorator that records tool calls."""

from app.application.tracing.recorder import Clock, SystemClock, TraceRecorder
from app.domain.tracing.models import ToolCall, TraceEventStatus
from app.infrastructure.search.provider import SearchProvider


class TracingSearchProvider:
    """Wrap a SearchProvider and record each call as a ToolCall event.

    Implements the same SearchProvider contract as the wrapped instance, so it
    is a drop-in replacement wherever a SearchProvider is expected. Agent code
    (RetrievalAgent, etc.) requires no changes to be traced.
    """

    def __init__(
        self,
        search_provider: SearchProvider,
        recorder: TraceRecorder,
        clock: Clock | None = None,
    ) -> None:
        self.search_provider = search_provider
        self.recorder = recorder
        self.clock = clock or SystemClock()

    def search(self, query: str) -> list[dict[str, str]]:
        """Search, recording the call as a trace event regardless of outcome."""
        started_at = self.clock.now()

        try:
            results = self.search_provider.search(query)
        except Exception as exc:
            completed_at = self.clock.now()

            self.recorder.record_tool_call(
                label="search",
                started_at=started_at,
                completed_at=completed_at,
                tool_call=ToolCall(
                    tool_name="search",
                    arguments={"query": query},
                    result_summary="no results: call raised an exception",
                    status=TraceEventStatus.FAILED,
                    error=f"{type(exc).__name__}: {exc}",
                ),
            )

            raise

        completed_at = self.clock.now()

        self.recorder.record_tool_call(
            label="search",
            started_at=started_at,
            completed_at=completed_at,
            tool_call=ToolCall(
                tool_name="search",
                arguments={"query": query},
                result_summary=f"{len(results)} result(s) returned",
                status=TraceEventStatus.SUCCESS,
            ),
        )

        return results
