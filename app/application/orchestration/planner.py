"""Planning services for ResearchOS."""

from app.application.orchestration.planning import DeterministicPlanner
from app.domain.research.models import ResearchRequest, ResearchTask


def plan_research(request: ResearchRequest) -> list[ResearchTask]:
    """Create a deterministic research plan from a validated request."""
    return DeterministicPlanner().plan(request)
