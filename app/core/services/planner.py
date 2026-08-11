"""Planning services for ResearchOS."""

from app.core.models.research import ResearchRequest, ResearchTask
from app.core.services.planning import DeterministicPlanner


def plan_research(request: ResearchRequest) -> list[ResearchTask]:
    """Create a deterministic research plan from a validated request."""
    return DeterministicPlanner().plan(request)
