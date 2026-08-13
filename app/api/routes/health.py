"""Health API route."""

from fastapi import APIRouter

from app.api.schemas import HealthResponse


def create_router() -> APIRouter:
    """Create the health router."""
    router = APIRouter()

    @router.get(
        "/health",
        response_model=HealthResponse,
    )
    def health() -> HealthResponse:
        """Return the service health status."""
        return HealthResponse(status="ok")

    return router
