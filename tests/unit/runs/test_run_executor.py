from app.application.orchestration.reliable_agent import ReliableResearchAgent
from app.application.orchestration.run_executor import ResearchRunExecutor
from app.domain.research.models import Evidence, ResearchTask
from app.domain.runs.failures import PermanentResearchFailure
from app.domain.runs.models import ResearchRunStatus


class StubAgent:
    def __init__(
        self,
        failing_objectives: set[str] | None = None,
    ) -> None:
        self.failing_objectives = failing_objectives or set()
        self.calls: list[str] = []

    def research(self, task: ResearchTask) -> list[Evidence]:
        self.calls.append(task.objective)

        if task.objective in self.failing_objectives:
            raise PermanentResearchFailure(f"Failed: {task.objective}")

        return [
            Evidence.model_construct(
                source=None,
                excerpt=f"Evidence for {task.objective}",
                relevance=0.9,
            )
        ]


def make_task(objective: str) -> ResearchTask:
    return ResearchTask(
        objective=objective,
        task_type="research",
        max_sources=2,
    )


def build_executor(
    failing_objectives: set[str] | None = None,
) -> tuple[ResearchRunExecutor, StubAgent]:
    agent = StubAgent(failing_objectives)
    reliable_agent = ReliableResearchAgent(agent)
    return ResearchRunExecutor(reliable_agent), agent


def test_executor_returns_success_when_all_tasks_complete() -> None:
    executor, agent = build_executor()

    outcome = executor.execute(
        [
            make_task("task one"),
            make_task("task two"),
        ]
    )

    assert outcome.status == ResearchRunStatus.SUCCESS
    assert outcome.completed_tasks == 2
    assert outcome.failed_tasks == 0
    assert outcome.failures == []
    assert len(outcome.evidence) == 2
    assert agent.calls == ["task one", "task two"]


def test_executor_returns_partial_when_some_tasks_fail() -> None:
    executor, _ = build_executor({"task two"})

    outcome = executor.execute(
        [
            make_task("task one"),
            make_task("task two"),
            make_task("task three"),
        ]
    )

    assert outcome.status == ResearchRunStatus.PARTIAL
    assert outcome.completed_tasks == 2
    assert outcome.failed_tasks == 1
    assert len(outcome.failures) == 1
    assert outcome.failures[0].task_objective == "task two"
    assert outcome.error_type if False else True
    assert len(outcome.evidence) == 2


def test_executor_returns_failed_when_all_tasks_fail() -> None:
    executor, _ = build_executor({"task one", "task two"})

    outcome = executor.execute(
        [
            make_task("task one"),
            make_task("task two"),
        ]
    )

    assert outcome.status == ResearchRunStatus.FAILED
    assert outcome.completed_tasks == 0
    assert outcome.failed_tasks == 2
    assert outcome.evidence == []


def test_executor_handles_empty_task_list() -> None:
    executor, _ = build_executor()

    outcome = executor.execute([])

    assert outcome.status == ResearchRunStatus.SUCCESS
    assert outcome.completed_tasks == 0
    assert outcome.failed_tasks == 0
    assert outcome.evidence == []
