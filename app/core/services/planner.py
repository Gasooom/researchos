"""Planning services for ResearchOS."""

from app.core.models.research import ResearchRequest, ResearchTask


def plan_research(request: ResearchRequest) -> list[ResearchTask]:
    """Create focused research tasks from a validated research request."""
    max_sources_per_task = request.max_sources

    return [
        ResearchTask(
            objective=f"Investigate the main aspects of: {request.question}",
            task_type="research",
            max_sources=max_sources_per_task,
        )
    ]
