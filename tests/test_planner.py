from app.core.models.research import ResearchRequest
from app.core.services.planner import plan_research


def test_plan_research_creates_tasks_from_request() -> None:
    request = ResearchRequest(
        question="What are the main challenges of AI agent reliability?"
    )

    tasks = plan_research(request)

    assert len(tasks) >= 1
    assert all(task.objective for task in tasks)
    assert all(task.task_type for task in tasks)


def test_plan_research_preserves_research_focus() -> None:
    request = ResearchRequest(
        question="How do multi-agent systems improve research workflows?"
    )

    tasks = plan_research(request)

    assert len(tasks) >= 1

    combined = " ".join(task.objective.lower() for task in tasks)

    assert "multi-agent" in combined or "research" in combined


def test_plan_research_respects_request_source_limit() -> None:
    request = ResearchRequest(
        question="What are the main challenges of AI agent reliability?",
        max_sources=7,
    )

    tasks = plan_research(request)

    assert all(task.max_sources <= request.max_sources for task in tasks)
