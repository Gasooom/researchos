"""FastAPI application factory for ResearchOS."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import create_router as create_health_router
from app.api.routes.research import create_router as create_research_router
from app.api.routes.runs import create_router as create_runs_router
from app.api.routes.ui import create_router as create_ui_router
from app.api.routes.workspace import (
    create_router as create_workspace_router,
)
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(create_health_router())
    app.include_router(create_research_router(service))
    app.include_router(create_runs_router(run_repository))
    app.include_router(create_ui_router(service))
    app.include_router(create_workspace_router(service))

    return app
