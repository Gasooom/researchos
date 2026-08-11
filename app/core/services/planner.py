"""Planning services for ResearchOS."""

from app.core.models.research import ResearchRequest, ResearchTask


def plan_research(request: ResearchRequest) -> list[ResearchTask]:
    """Create focused research tasks from a validated research request."""
    task_templates = (
        (
            "scope",
            f"Investigate the main aspects of: {request.question}",
        ),
        (
            "evidence",
            f"Find evidence and supporting findings about: {request.question}",
        ),
        (
            "evaluation",
            f"Evaluate the key findings and limitations related to: {request.question}",
        ),
    )

    return [
        ResearchTask(
            objective=objective,
            task_type=task_type,
            max_sources=request.max_sources,
        )
        for task_type, objective in task_templates
    ]
