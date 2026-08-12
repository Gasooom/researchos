"""Run observability services for ResearchOS."""

from app.domain.runs.models import ResearchRunOutcome
from app.domain.runs.observability import RunObservation


class RunObserver:
    """Create operational observations from research run outcomes."""

    def observe(
        self,
        outcome: ResearchRunOutcome,
        duration_seconds: float,
    ) -> RunObservation:
        """Create an operational observation for a completed run."""
        if duration_seconds < 0:
            raise ValueError("duration_seconds must not be negative")

        total_tasks = outcome.completed_tasks + outcome.failed_tasks

        return RunObservation(
            duration_seconds=duration_seconds,
            total_tasks=total_tasks,
            completed_tasks=outcome.completed_tasks,
            failed_tasks=outcome.failed_tasks,
            status=outcome.status,
        )
