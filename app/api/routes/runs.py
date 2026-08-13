"""Research run API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.schemas import RunResponse
from app.domain.runs.repository import ResearchRunRepository


def create_router(
    repository: ResearchRunRepository,
) -> APIRouter:
    """Create run routes bound to a run repository."""
    router = APIRouter(
        prefix="/runs",
        tags=["runs"],
    )

    @router.get(
        "/{run_id}",
        response_model=RunResponse,
    )
    def get_run(run_id: UUID) -> RunResponse:
        """Return a persisted research run."""
        run = repository.get(run_id)

        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="research run not found",
            )

        return RunResponse(run=run)

    return router
