import json

import pytest

from app.application.agents.llm_analysis import LLMAnalysisAgent
from app.application.agents.roles import AgentRole
from app.domain.research.analysis import AnalysisResult
from app.domain.research.models import Evidence, ResearchTask, Source


def make_evidence() -> list[Evidence]:
    source = Source(
        title="Example Research",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at="2026-08-13T09:00:00Z",
    )

    return [
        Evidence(
            source=source,
            excerpt="Structured evaluation improves AI system reliability.",
            relevance=0.92,
        ),
        Evidence(
            source=source,
            excerpt="Traceable execution helps identify research failures.",
            relevance=0.87,
        ),
    ]


class StubLLM:
    """Deterministic provider for LLM analysis tests."""

    def __init__(self) -> None:
        self.prompt: str | None = None

    def generate(self, prompt: str) -> list[dict[str, str]]:
        self.prompt = prompt

        return [
            {
                "analysis": json.dumps(
                    {
                        "summary": (
                            "The evidence indicates that structured "
                            "evaluation and traceable execution improve "
                            "research reliability."
                        ),
                        "key_points": [
                            "Structured evaluation improves reliability.",
                            "Traceable execution helps identify failures.",
                        ],
                        "confidence": 0.91,
                    }
                )
            }
        ]


def test_llm_analysis_agent_has_analysis_role() -> None:
    agent = LLMAnalysisAgent(StubLLM())

    assert agent.role == AgentRole.ANALYSIS


def test_llm_analysis_agent_returns_valid_analysis() -> None:
    provider = StubLLM()
    agent = LLMAnalysisAgent(provider)

    task = ResearchTask(
        objective="Investigate AI research reliability.",
        task_type="reliability",
        max_sources=2,
    )

    result = agent.execute(
        task=task,
        evidence=make_evidence(),
    )

    assert isinstance(result, AnalysisResult)
    assert result.summary.startswith("The evidence indicates")
    assert len(result.key_points) == 2
    assert result.confidence == pytest.approx(0.91)


def test_llm_analysis_agent_passes_task_and_evidence_to_provider() -> None:
    provider = StubLLM()
    agent = LLMAnalysisAgent(provider)

    task = ResearchTask(
        objective="Investigate AI research reliability.",
    )

    evidence = make_evidence()

    agent.execute(
        task=task,
        evidence=evidence,
    )

    assert provider.prompt is not None
    assert task.objective in provider.prompt
    assert evidence[0].excerpt in provider.prompt
    assert evidence[1].excerpt in provider.prompt


def test_llm_analysis_prompt_requires_evidence_grounding() -> None:
    provider = StubLLM()
    agent = LLMAnalysisAgent(provider)

    agent.execute(
        task=ResearchTask(
            objective="Investigate AI research reliability.",
        ),
        evidence=make_evidence(),
    )

    assert provider.prompt is not None
    assert "ONLY the provided evidence" in provider.prompt
    assert "Do not add facts that are not supported by the evidence" in (
        provider.prompt
    )
    assert "Do not use outside knowledge" in provider.prompt


def test_llm_analysis_prompt_requires_uncertainty_preservation() -> None:
    provider = StubLLM()
    agent = LLMAnalysisAgent(provider)

    agent.execute(
        task=ResearchTask(
            objective="Investigate uncertain AI reliability evidence.",
        ),
        evidence=make_evidence(),
    )

    assert provider.prompt is not None
    assert "preserve that uncertainty" in provider.prompt
    assert "incomplete or conflicting" in provider.prompt


def test_llm_analysis_agent_rejects_empty_evidence() -> None:
    agent = LLMAnalysisAgent(StubLLM())

    task = ResearchTask(
        objective="Investigate AI research reliability.",
    )

    with pytest.raises(ValueError, match="evidence must not be empty"):
        agent.execute(
            task=task,
            evidence=[],
        )


def test_llm_analysis_agent_rejects_missing_analysis_field() -> None:
    class InvalidProvider:
        def generate(self, prompt: str) -> list[dict[str, str]]:
            return [{"unexpected": "value"}]

    agent = LLMAnalysisAgent(InvalidProvider())

    task = ResearchTask(
        objective="Investigate AI research reliability.",
    )

    with pytest.raises(
        ValueError,
        match="must contain 'analysis'",
    ):
        agent.execute(
            task=task,
            evidence=make_evidence(),
        )


def test_llm_analysis_agent_rejects_invalid_json() -> None:
    class InvalidProvider:
        def generate(self, prompt: str) -> list[dict[str, str]]:
            return [{"analysis": "not-json"}]

    agent = LLMAnalysisAgent(InvalidProvider())

    task = ResearchTask(
        objective="Investigate AI research reliability.",
    )

    with pytest.raises(
        ValueError,
        match="returned invalid JSON",
    ):
        agent.execute(
            task=task,
            evidence=make_evidence(),
        )


def test_llm_analysis_agent_rejects_invalid_domain_output() -> None:
    class InvalidProvider:
        def generate(self, prompt: str) -> list[dict[str, str]]:
            return [
                {
                    "analysis": json.dumps(
                        {
                            "summary": "",
                            "key_points": [],
                            "confidence": 2.0,
                        }
                    )
                }
            ]

    agent = LLMAnalysisAgent(InvalidProvider())

    task = ResearchTask(
        objective="Investigate AI research reliability.",
    )

    with pytest.raises(ValueError):
        agent.execute(
            task=task,
            evidence=make_evidence(),
        )
