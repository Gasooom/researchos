import pytest

from app.application.orchestration.reliable_agent import ReliableResearchAgent
from app.domain.research.models import ResearchTask
from app.domain.runs.failures import (
    PermanentResearchFailure,
    TransientResearchFailure,
)


class StubAgent:
    def __init__(
        self,
        failures_before_success: int = 0,
        failure_type: type[Exception] = TransientResearchFailure,
    ) -> None:
        self.failures_before_success = failures_before_success
        self.failure_type = failure_type
        self.calls = 0

    def research(self, task: ResearchTask) -> list:
        self.calls += 1

        if self.calls <= self.failures_before_success:
            raise self.failure_type("research failure")

        return []


def make_task() -> ResearchTask:
    return ResearchTask(
        objective="Investigate AI agent reliability.",
        task_type="reliability",
        max_sources=3,
    )


def test_reliable_agent_succeeds_without_retry() -> None:
    agent = StubAgent()
    reliable_agent = ReliableResearchAgent(agent)

    result = reliable_agent.research(make_task())

    assert result == []
    assert agent.calls == 1


def test_reliable_agent_retries_transient_failure() -> None:
    agent = StubAgent(
        failures_before_success=2,
        failure_type=TransientResearchFailure,
    )
    reliable_agent = ReliableResearchAgent(
        agent,
        max_attempts=3,
    )

    result = reliable_agent.research(make_task())

    assert result == []
    assert agent.calls == 3


def test_reliable_agent_stops_on_permanent_failure() -> None:
    agent = StubAgent(
        failures_before_success=1,
        failure_type=PermanentResearchFailure,
    )
    reliable_agent = ReliableResearchAgent(
        agent,
        max_attempts=3,
    )

    with pytest.raises(PermanentResearchFailure):
        reliable_agent.research(make_task())

    assert agent.calls == 1


def test_reliable_agent_raises_after_transient_attempts_are_exhausted() -> None:
    agent = StubAgent(
        failures_before_success=3,
        failure_type=TransientResearchFailure,
    )
    reliable_agent = ReliableResearchAgent(
        agent,
        max_attempts=3,
    )

    with pytest.raises(TransientResearchFailure):
        reliable_agent.research(make_task())

    assert agent.calls == 3


def test_reliable_agent_validates_attempts() -> None:
    agent = StubAgent()

    with pytest.raises(ValueError, match="max_attempts"):
        ReliableResearchAgent(agent, max_attempts=0)


def test_reliable_agent_validates_retry_delay() -> None:
    agent = StubAgent()

    with pytest.raises(ValueError, match="retry_delay"):
        ReliableResearchAgent(agent, retry_delay=-1)
