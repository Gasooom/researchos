from app.core.models.research import ResearchRequest, ResearchTask
from app.core.services.planner import plan_research
from app.core.services.planning import DeterministicPlanner, PlannerStrategy


class StubPlanner(PlannerStrategy):
    """Test implementation of the planner strategy contract."""

    def plan(self, request: ResearchRequest) -> list[ResearchTask]:
        return [
            ResearchTask(
                objective=f"Research: {request.question}",
                task_type="research",
                max_sources=request.max_sources,
            )
        ]


def test_planner_strategy_can_be_implemented() -> None:
    request = ResearchRequest(
        question="What are the main challenges of AI agent reliability?"
    )

    planner = StubPlanner()

    tasks = planner.plan(request)

    assert len(tasks) == 1
    assert tasks[0].objective == (
        "Research: What are the main challenges of AI agent reliability?"
    )


def test_planner_strategy_preserves_request_constraints() -> None:
    request = ResearchRequest(
        question="How do multi-agent systems improve research workflows?",
        max_sources=7,
    )

    planner = StubPlanner()

    tasks = planner.plan(request)

    assert tasks
    assert all(task.max_sources == 7 for task in tasks)


def test_deterministic_planner_implements_strategy() -> None:
    planner = DeterministicPlanner()

    assert isinstance(planner, PlannerStrategy)


def test_deterministic_planner_matches_existing_planner_behavior() -> None:
    request = ResearchRequest(
        question="What are the main challenges of AI agent reliability?",
        max_sources=7,
    )

    planner = DeterministicPlanner()

    strategy_tasks = planner.plan(request)
    existing_tasks = plan_research(request)

    assert strategy_tasks == existing_tasks
