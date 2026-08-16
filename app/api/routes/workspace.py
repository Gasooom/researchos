"""Research workspace API routes."""

from fastapi import APIRouter

from app.api.workspace import WorkspaceResponse
from app.application.research_service import ResearchApplicationService
from app.domain.research.models import ResearchRequest


def create_router(
    service: ResearchApplicationService,
) -> APIRouter:
    """Create workspace routes."""
    router = APIRouter(
        prefix="/workspace",
        tags=["workspace"],
    )

    @router.post(
        "",
        response_model=WorkspaceResponse,
    )
    def run_workspace(
        question: str,
        max_sources: int = 5,
    ) -> WorkspaceResponse:
        """Execute research and return the complete workspace payload."""
        request = ResearchRequest(
            question=question,
            max_sources=max_sources,
        )

        (
            result,
            execution,
            agents,
            evaluation,
            observation,
        ) = service.execute_workspace(request)

        return WorkspaceResponse(
            result=result,
            execution=execution,
            agents=agents,
            evaluation=evaluation,
            observation=observation,
        )

    return router
