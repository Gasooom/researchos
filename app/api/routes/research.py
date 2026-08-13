"""Research API routes."""

from fastapi import APIRouter, status

from app.api.schemas import ResearchRequestSchema, ResearchResponse
from app.application.research_service import ResearchApplicationService
from app.domain.research.models import ResearchRequest


def create_router(
    service: ResearchApplicationService,
) -> APIRouter:
    """Create research routes bound to an application service."""
    router = APIRouter(
        prefix="/research",
        tags=["research"],
    )

    @router.post(
        "",
        response_model=ResearchResponse,
        status_code=status.HTTP_200_OK,
    )
    def run_research(
        request: ResearchRequestSchema,
    ) -> ResearchResponse:
        """Execute a research request."""
        domain_request = ResearchRequest(
            question=request.question,
            max_sources=request.max_sources,
        )

        result = service.execute(domain_request)

        return ResearchResponse(result=result)

    return router
