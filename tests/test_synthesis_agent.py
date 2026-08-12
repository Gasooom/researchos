from datetime import UTC, datetime

import pytest

from app.core.models.analysis import AnalysisResult
from app.core.models.research import Evidence, ResearchTask, Source
from app.core.services.agent_roles import AgentRole
from app.core.services.synthesis_agent import SynthesisAgent


def make_source() -> Source:
    return Source(
        title="Example Research",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at=datetime.now(UTC),
    )


def make_evidence(
    excerpt: str,
    relevance: float,
) -> Evidence:
    return Evidence(
        source=make_source(),
        excerpt=excerpt,
        relevance=relevance,
    )


def make_task() -> ResearchTask:
    return ResearchTask(
        objective="Investigate AI agent reliability.",
        task_type="synthesis",
        max_sources=5,
    )


def make_analysis() -> AnalysisResult:
    return AnalysisResult(
        summary="AI agent reliability depends on evaluation.",
        key_points=[
            "AI agents can fail unpredictably.",
            "Evaluation improves agent reliability.",
        ],
        confidence=0.92,
    )


def test_synthesis_agent_has_synthesis_role() -> None:
    agent = SynthesisAgent()

    assert agent.role == AgentRole.SYNTHESIS


def test_synthesis_agent_produces_structured_result() -> None:
    agent = SynthesisAgent()

    evidence = [
        make_evidence(
            "AI agents can fail unpredictably.",
            0.92,
        ),
        make_evidence(
            "Evaluation improves agent reliability.",
            0.81,
        ),
    ]

    result = agent.execute(
        task=make_task(),
        evidence=evidence,
        analysis=make_analysis(),
    )

    assert result.answer.startswith("Based on the available evidence,")
    assert result.supporting_points == [
        "AI agents can fail unpredictably.",
        "Evaluation improves agent reliability.",
    ]
    assert result.confidence == 0.92


def test_synthesis_agent_preserves_analysis_confidence() -> None:
    agent = SynthesisAgent()

    analysis = AnalysisResult(
        summary="Strong evidence supports the conclusion.",
        key_points=["Strong evidence supports the conclusion."],
        confidence=0.97,
    )

    result = agent.execute(
        task=make_task(),
        evidence=[make_evidence("Strong evidence.", 0.97)],
        analysis=analysis,
    )

    assert result.confidence == 0.97


def test_synthesis_agent_rejects_empty_evidence() -> None:
    agent = SynthesisAgent()

    with pytest.raises(ValueError, match="evidence must not be empty"):
        agent.execute(
            task=make_task(),
            evidence=[],
            analysis=make_analysis(),
        )


def test_analysis_result_rejects_empty_key_point() -> None:
    with pytest.raises(
        ValueError,
        match="key_points must not contain empty values",
    ):
        AnalysisResult(
            summary="No usable analysis.",
            key_points=[""],
            confidence=0.0,
        )
