"""Run observability models for ResearchOS."""

from pydantic import BaseModel, Field

from app.core.models.run import ResearchRunStatus


class RunObservation(BaseModel):
    """Operational observation captured for one research run."""

    duration_seconds: float = Field(ge=0.0)
    total_tasks: int = Field(ge=0)
    completed_tasks: int = Field(ge=0)
    failed_tasks: int = Field(ge=0)
    status: ResearchRunStatus

    @property
    def success_rate(self) -> float:
        """Return the fraction of tasks completed successfully."""
        if self.total_tasks == 0:
            return 0.0

        return self.completed_tasks / self.total_tasks

    @property
    def failure_rate(self) -> float:
        """Return the fraction of tasks that failed."""
        if self.total_tasks == 0:
            return 0.0

        return self.failed_tasks / self.total_tasks
