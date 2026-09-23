"""Minimal browser UI for ResearchOS."""

import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.application.research_service import ResearchApplicationService
from app.domain.research.models import ResearchRequest

logger = logging.getLogger(__name__)


def create_router(
    service: ResearchApplicationService,
) -> APIRouter:
    """Create the ResearchOS browser UI router."""
    router = APIRouter(
        prefix="/ui",
        tags=["ui"],
    )

    templates = Jinja2Templates(
        directory="app/templates",
    )

    @router.get(
        "/",
        response_class=HTMLResponse,
    )
    def home(request: Request) -> HTMLResponse:
        """Render the ResearchOS home page."""
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "result": None,
                "error": None,
            },
        )

    @router.post(
        "/research",
        response_class=HTMLResponse,
    )
    def run_research(
        request: Request,
        question: str = Form(...),
    ) -> HTMLResponse:
        """Run research and render the result."""
        try:
            result = service.execute(
                ResearchRequest(
                    question=question,
                    max_sources=3,
                )
            )

            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "result": result,
                    "error": None,
                },
            )
        except Exception:
            logger.exception("UI research request failed for question: %s", question)

            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "result": None,
                    "error": "Something went wrong while running this research "
                    "request. Check the server logs for details.",
                },
                status_code=500,
            )

    return router
