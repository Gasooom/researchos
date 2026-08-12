"""LLM-backed planning services for ResearchOS."""

from typing import Protocol

from pydantic import BaseModel, Field

from app.application.orchestration.planning import PlannerStrategy
from app.domain.research.models import ResearchRequest, ResearchTask


class LLMTaskOutput(BaseModel):
    """Validated task data returned by an LLM provider."""

    objective: str = Field(min_length=1)
    task_type: str = Field(min_length=1)


class LLMProvider(Protocol):
    """Protocol for providers capable of generating planner output."""

    def generate(self, prompt: str) -> list[dict[str, str]]:
        """Generate structured planning data from a prompt."""
        ...


class LLMPlanner(PlannerStrategy):
    """Planner that converts provider-generated tasks into domain models."""

    def __init__(self, provider: LLMProvider) -> None:
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
