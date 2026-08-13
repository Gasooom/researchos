"""FastAPI application factory for ResearchOS."""

from fastapi import FastAPI

from app.api.routes.health import create_router as create_health_router
from app.api.routes.research import create_router as create_research_router
from app.api.routes.runs import create_router as create_runs_router
from app.application.research_service import ResearchApplicationService
from app.domain.runs.repository import ResearchRunRepository


def create_app(
    service: ResearchApplicationService,
    run_repository: ResearchRunRepository,
) -> FastAPI:
    """Create the ResearchOS HTTP application."""
    app = FastAPI(
        title="ResearchOS",
        version="0.1.0",
        description="Evidence-grounded multi-agent research system.",
    )

    app.include_router(create_health_router())
    app.include_router(create_research_router(service))
    app.include_router(create_runs_router(run_repository))

    return app
