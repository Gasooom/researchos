"""Planning strategy implementations for ResearchOS."""

from abc import ABC, abstractmethod

from app.domain.research.models import ResearchRequest, ResearchTask


class PlannerStrategy(ABC):
    """Contract for implementations that turn requests into research tasks."""

    @abstractmethod
    def plan(self, request: ResearchRequest) -> list[ResearchTask]:
        """Create focused research tasks from a validated request."""
        raise NotImplementedError


class DeterministicPlanner(PlannerStrategy):
    """Deterministic planner using predefined research dimensions."""

    def plan(self, request: ResearchRequest) -> list[ResearchTask]:
        """Create a deterministic research plan."""
        task_templates = (
            (
                "scope",
                f"Investigate the main aspects of: {request.question}",
            ),
            (
                "evidence",
                f"Find evidence and supporting findings about: {request.question}",
            ),
            (
                "evaluation",
                "Evaluate the key findings and limitations related to: "
                f"{request.question}",
            ),
        )

        return [
            ResearchTask(
                objective=objective,
                task_type=task_type,
                max_sources=request.max_sources,
            )
            for task_type, objective in task_templates
        ]
