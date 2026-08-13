"""ResearchOS application entry point."""

from app.api.app import create_app
from app.bootstrap.container import create_research_service
from app.core.config import get_settings
from app.infrastructure.persistence.sqlite_run_repository import (
    SQLiteResearchRunRepository,
)


def create_application():
    """Build the production FastAPI application."""
    settings = get_settings()

    service = create_research_service(settings)

    repository = SQLiteResearchRunRepository(
        database_path=settings.research_database_path,
    )

    return create_app(
        service=service,
        run_repository=repository,
    )


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
