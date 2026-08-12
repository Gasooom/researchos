from datetime import UTC, datetime

from app.core.models.research import Evidence, ResearchTask, Source
from app.core.services.agent_roles import AgentRole
from app.core.services.analysis_agent import AnalysisAgent


def make_evidence(
    excerpt: str,
    relevance: float,
) -> Evidence:
    source = Source(
        title="Example Research",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at=datetime.now(UTC),
    )

    return Evidence(
        source=source,
        excerpt=excerpt,
        relevance=relevance,
    )


def make_task() -> ResearchTask:
    return ResearchTask(
        objective="Investigate AI agent reliability.",
        task_type="analysis",
        max_sources=5,
    )


def test_analysis_agent_has_analysis_role() -> None:
    agent = AnalysisAgent()

    assert agent.role == AgentRole.ANALYSIS


def test_analysis_agent_produces_structured_analysis() -> None:
    agent = AnalysisAgent()

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
    )

    assert result.summary == (
        "Analysis of 2 evidence items for: Investigate AI agent reliability."
    )
    assert result.key_points == [
        "AI agents can fail unpredictably.",
        "Evaluation improves agent reliability.",
    ]
    assert result.confidence == 0.92


def test_analysis_agent_uses_strongest_relevance_as_confidence() -> None:
    agent = AnalysisAgent()

    evidence = [
        make_evidence("Lower relevance evidence.", 0.55),
        make_evidence("Strong evidence.", 0.97),
        make_evidence("Medium evidence.", 0.72),
    ]

    result = agent.execute(
        task=make_task(),
        evidence=evidence,
    )

    assert result.confidence == 0.97


def test_analysis_agent_rejects_empty_evidence() -> None:
    agent = AnalysisAgent()

    try:
        agent.execute(
            task=make_task(),
            evidence=[],
        )
    except ValueError as exc:
        assert str(exc) == "evidence must not be empty"
    else:
        raise AssertionError("Expected ValueError")
