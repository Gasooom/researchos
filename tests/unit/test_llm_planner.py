import pytest
from pydantic import ValidationError

from app.domain.research.models import ResearchRequest, ResearchTask
from app.infrastructure.llm.planner import LLMPlanner


class StubLLM:
    """Deterministic test double for an LLM provider."""

    def generate(self, prompt: str) -> list[dict[str, str]]:
        return [
            {
                "objective": "Investigate AI agent reliability challenges.",
                "task_type": "reliability",
            },
            {
                "objective": "Evaluate methods for measuring AI agent reliability.",
                "task_type": "evaluation",
            },
        ]


def test_llm_planner_implements_planner_strategy() -> None:
    planner = LLMPlanner(provider=StubLLM())

    assert isinstance(planner, LLMPlanner)
    assert hasattr(planner, "plan")


def test_llm_planner_converts_provider_output_to_research_tasks() -> None:
    planner = LLMPlanner(provider=StubLLM())

    request = ResearchRequest(
        question="What are the main challenges of AI agent reliability?",
        max_sources=7,
    )

    tasks = planner.plan(request)

    assert tasks == [
        ResearchTask(
            objective="Investigate AI agent reliability challenges.",
            task_type="reliability",
            max_sources=7,
        ),
        ResearchTask(
            objective="Evaluate methods for measuring AI agent reliability.",
            task_type="evaluation",
            max_sources=7,
        ),
    ]


def test_llm_planner_passes_request_to_provider() -> None:
    class RecordingLLM:
        def __init__(self) -> None:
            self.prompt = None

        def generate(self, prompt: str) -> list[dict[str, str]]:
            self.prompt = prompt
            return [
                {
                    "objective": "Research reliability.",
                    "task_type": "research",
                }
            ]

    provider = RecordingLLM()
    planner = LLMPlanner(provider=provider)

    request = ResearchRequest(question="How reliable are AI agents?")

    planner.plan(request)

    assert provider.prompt is not None
    assert "How reliable are AI agents?" in provider.prompt


def test_llm_planner_rejects_missing_objective() -> None:
    class InvalidLLM:
        def generate(self, prompt: str) -> list[dict[str, str]]:
            return [{"task_type": "research"}]

    planner = LLMPlanner(provider=InvalidLLM())

    request = ResearchRequest(question="How reliable are AI agents?")

    with pytest.raises(ValidationError):
        planner.plan(request)


def test_llm_planner_rejects_empty_objective() -> None:
    class InvalidLLM:
        def generate(self, prompt: str) -> list[dict[str, str]]:
            return [
                {
                    "objective": "",
                    "task_type": "research",
                }
            ]

    planner = LLMPlanner(provider=InvalidLLM())

    request = ResearchRequest(question="How reliable are AI agents?")

    with pytest.raises(ValidationError):
        planner.plan(request)


def test_llm_planner_rejects_empty_task_type() -> None:
    class InvalidLLM:
        def generate(self, prompt: str) -> list[dict[str, str]]:
            return [
                {
                    "objective": "Research reliability.",
                    "task_type": "",
                }
            ]

    planner = LLMPlanner(provider=InvalidLLM())

    request = ResearchRequest(question="How reliable are AI agents?")

    with pytest.raises(ValidationError):
        planner.plan(request)


def test_llm_planner_works_with_provider_adapter() -> None:
    from app.infrastructure.llm.provider import LLMProviderAdapter

    class FakeClient:
        def generate(self, prompt: str) -> list[dict[str, str]]:
            return [
                {
                    "objective": "Research AI agent reliability.",
                    "task_type": "research",
                }
            ]

    provider = LLMProviderAdapter(client=FakeClient())
    planner = LLMPlanner(provider=provider)

    request = ResearchRequest(
        question="How reliable are AI agents?",
        max_sources=5,
    )

    tasks = planner.plan(request)

    assert tasks == [
        ResearchTask(
            objective="Research AI agent reliability.",
            task_type="research",
            max_sources=5,
        )
    ]
