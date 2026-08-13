import json

import pytest

from app.application.agents.llm_synthesis import LLMSynthesisAgent
from app.application.agents.roles import AgentRole
from app.domain.research.analysis import AnalysisResult
from app.domain.research.models import Evidence, ResearchTask, Source
from app.domain.research.synthesis import SynthesisResult


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


def make_analysis() -> AnalysisResult:
    return AnalysisResult(
        summary=(
            "The evidence indicates that structured evaluation and "
            "traceable execution improve research reliability."
        ),
        key_points=[
            "Structured evaluation improves reliability.",
            "Traceable execution helps identify failures.",
        ],
        confidence=0.91,
    )


class StubLLM:
    """Deterministic provider for LLM synthesis tests."""

    def __init__(self) -> None:
        self.prompt: str | None = None

    def generate(self, prompt: str) -> list[dict[str, str]]:
        self.prompt = prompt

        return [
            {
                "synthesis": json.dumps(
                    {
                        "answer": (
                            "The evidence suggests that structured "
                            "evaluation and traceable execution improve "
                            "research reliability."
                        ),
                        "supporting_points": [
                            "Structured evaluation improves reliability.",
                            "Traceable execution helps identify failures.",
                        ],
                        "confidence": 0.91,
                    }
                )
            }
        ]


def test_llm_synthesis_agent_has_synthesis_role() -> None:
    agent = LLMSynthesisAgent(StubLLM())

    assert agent.role == AgentRole.SYNTHESIS


def test_llm_synthesis_agent_returns_valid_synthesis() -> None:
    agent = LLMSynthesisAgent(StubLLM())

    task = ResearchTask(
        objective="Investigate AI research reliability.",
        task_type="reliability",
        max_sources=2,
    )

    result = agent.execute(
        task=task,
        evidence=make_evidence(),
        analysis=make_analysis(),
    )

    assert isinstance(result, SynthesisResult)
    assert result.answer.startswith("The evidence suggests")
    assert len(result.supporting_points) == 2
    assert result.confidence == pytest.approx(0.91)


def test_llm_synthesis_agent_passes_context_to_provider() -> None:
    provider = StubLLM()
    agent = LLMSynthesisAgent(provider)

    task = ResearchTask(
        objective="Investigate AI research reliability.",
    )
    evidence = make_evidence()
    analysis = make_analysis()

    agent.execute(
        task=task,
        evidence=evidence,
        analysis=analysis,
    )

    assert provider.prompt is not None
    assert task.objective in provider.prompt
    assert analysis.summary in provider.prompt
    assert analysis.key_points[0] in provider.prompt
    assert evidence[0].excerpt in provider.prompt
    assert evidence[1].excerpt in provider.prompt


def test_llm_synthesis_prompt_requires_evidence_grounding() -> None:
    provider = StubLLM()
    agent = LLMSynthesisAgent(provider)

    agent.execute(
        task=ResearchTask(
            objective="Investigate AI research reliability.",
        ),
        evidence=make_evidence(),
        analysis=make_analysis(),
    )

    assert provider.prompt is not None
    assert "ONLY from the supplied evidence and analysis" in provider.prompt
    assert "Do not introduce unsupported facts" in provider.prompt
    assert "outside knowledge" in provider.prompt


def test_llm_synthesis_prompt_requires_uncertainty_preservation() -> None:
    provider = StubLLM()
    agent = LLMSynthesisAgent(provider)

    agent.execute(
        task=ResearchTask(
            objective="Investigate uncertain AI reliability evidence.",
        ),
        evidence=make_evidence(),
        analysis=make_analysis(),
    )

    assert provider.prompt is not None
    assert "Preserve uncertainty" in provider.prompt
    assert "weak or incomplete evidence" in provider.prompt


def test_llm_synthesis_agent_rejects_empty_evidence() -> None:
    agent = LLMSynthesisAgent(StubLLM())

    task = ResearchTask(
        objective="Investigate AI research reliability.",
    )

    with pytest.raises(ValueError, match="evidence must not be empty"):
        agent.execute(
            task=task,
            evidence=[],
            analysis=make_analysis(),
        )


def test_llm_synthesis_agent_rejects_empty_analysis() -> None:
    agent = LLMSynthesisAgent(StubLLM())

    task = ResearchTask(
        objective="Investigate AI research reliability.",
    )

    analysis = AnalysisResult(
        summary="Valid summary.",
        key_points=["Valid key point."],
        confidence=0.8,
    )

    analysis.key_points.clear()

    with pytest.raises(
        ValueError,
        match="analysis must contain key points",
    ):
        agent.execute(
            task=task,
            evidence=make_evidence(),
            analysis=analysis,
        )


def test_llm_synthesis_agent_rejects_missing_synthesis_field() -> None:
    class InvalidProvider:
        def generate(self, prompt: str) -> list[dict[str, str]]:
            return [{"unexpected": "value"}]

    agent = LLMSynthesisAgent(InvalidProvider())

    task = ResearchTask(
        objective="Investigate AI research reliability.",
    )

    with pytest.raises(
        ValueError,
        match="must contain 'synthesis'",
    ):
        agent.execute(
            task=task,
            evidence=make_evidence(),
            analysis=make_analysis(),
        )


def test_llm_synthesis_agent_rejects_invalid_json() -> None:
    class InvalidProvider:
        def generate(self, prompt: str) -> list[dict[str, str]]:
            return [{"synthesis": "not-json"}]

    agent = LLMSynthesisAgent(InvalidProvider())

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
            analysis=make_analysis(),
        )


def test_llm_synthesis_agent_rejects_invalid_domain_output() -> None:
    class InvalidProvider:
        def generate(self, prompt: str) -> list[dict[str, str]]:
            return [
                {
                    "synthesis": json.dumps(
                        {
                            "answer": "",
                            "supporting_points": [],
                            "confidence": 2.0,
                        }
                    )
                }
            ]

    agent = LLMSynthesisAgent(InvalidProvider())

    task = ResearchTask(
        objective="Investigate AI research reliability.",
    )

    with pytest.raises(ValueError):
        agent.execute(
            task=task,
            evidence=make_evidence(),
            analysis=make_analysis(),
        )
