from datetime import UTC, datetime

from app.application.orchestration.research_service import build_research_result
from app.domain.research.models import (
    Claim,
    Evidence,
    ResearchRequest,
    Source,
)


def test_build_research_result_composes_valid_domain_objects() -> None:
    request = ResearchRequest(
        question="What are the main challenges of AI agent reliability?"
    )

    source = Source(
        title="AI Agent Reliability",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at=datetime.now(UTC),
    )

    evidence = Evidence(
        source=source,
        excerpt="Agent reliability remains an important deployment challenge.",
        relevance=0.92,
    )

    claim = Claim(
        statement="Agent reliability remains a deployment challenge.",
        evidence=[evidence],
    )

    result = build_research_result(
        request=request,
        claims=[claim],
        sources=[source],
    )

    assert result.question == "What are the main challenges of AI agent reliability?"
    assert result.claims == [claim]
    assert result.sources == [source]


def test_build_research_result_preserves_request_question() -> None:
    request = ResearchRequest(
        question="How do multi-agent systems improve research workflows?"
    )

    source = Source(
        title="Multi-Agent Research",
        url="https://example.com/multi-agent",
        publisher="Example Research",
        retrieved_at=datetime.now(UTC),
    )

    evidence = Evidence(
        source=source,
        excerpt="Multiple agents can divide research tasks.",
        relevance=0.88,
    )

    claim = Claim(
        statement="Task decomposition can improve research workflows.",
        evidence=[evidence],
    )

    result = build_research_result(
        request=request,
        claims=[claim],
        sources=[source],
    )

    assert result.question == request.question
