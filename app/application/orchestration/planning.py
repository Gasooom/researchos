"""Planning strategy implementations for ResearchOS."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

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


class LLMTaskOutput(BaseModel):
    """Validated task data returned by an LLM provider."""

    objective: str = Field(min_length=1)
    task_type: str = Field(min_length=1)


class LLMPlanner(PlannerStrategy):
    """Planner that converts provider-generated tasks into domain models."""

    def __init__(self, provider) -> None:
        self.provider = provider

    def plan(self, request: ResearchRequest) -> list[ResearchTask]:
        """Generate validated research tasks using the configured provider."""
        prompt = (
            "Create focused research tasks for the following research question:\n"
            f"{request.question}"
        )

        generated_tasks = self.provider.generate(prompt)

        validated_tasks = [
            LLMTaskOutput.model_validate(item) for item in generated_tasks
        ]

        return [
            ResearchTask(
                objective=item.objective,
                task_type=item.task_type,
                max_sources=request.max_sources,
            )
            for item in validated_tasks
        ]
