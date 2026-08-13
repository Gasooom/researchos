"""Application service for executing ResearchOS research use cases."""

from app.application.orchestration.research import ResearchOrchestrator
from app.domain.research.models import ResearchRequest, ResearchResult


class ResearchApplicationService:
    """Expose the research workflow as an application-level use case."""

    def __init__(
        self,
        orchestrator: ResearchOrchestrator,
    ) -> None:
        self.orchestrator = orchestrator

    def execute(
        self,
        request: ResearchRequest,
    ) -> ResearchResult:
        """Execute a research request through the orchestrator."""
        return self.orchestrator.run(request)
