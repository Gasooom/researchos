from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.core.models.research import (
    Claim,
    Evidence,
    ResearchRequest,
    ResearchResult,
    ResearchTask,
    Source,
)


def test_research_request_uses_defaults() -> None:
    request = ResearchRequest(question="What are the main risks of AI agents?")

    assert request.question == "What are the main risks of AI agents?"
    assert request.max_sources == 10
    assert request.depth == "standard"


def test_research_request_accepts_custom_values() -> None:
    request = ResearchRequest(
        question="Compare RAG and fine-tuning.",
        max_sources=20,
        depth="deep",
    )

    assert request.question == "Compare RAG and fine-tuning."
    assert request.max_sources == 20
    assert request.depth == "deep"


def test_research_request_rejects_empty_question() -> None:
    with pytest.raises(ValidationError):
        ResearchRequest(question="")


def test_research_request_rejects_whitespace_question() -> None:
    with pytest.raises(ValidationError):
        ResearchRequest(question="   ")


def test_research_request_rejects_invalid_source_limit() -> None:
    with pytest.raises(ValidationError):
        ResearchRequest(
            question="What are the main risks of AI agents?",
            max_sources=0,
        )

    with pytest.raises(ValidationError):
        ResearchRequest(
            question="What are the main risks of AI agents?",
            max_sources=51,
        )


def test_research_task_uses_defaults() -> None:
    task = ResearchTask(objective="Find evidence about AI agent reliability.")

    assert task.objective == "Find evidence about AI agent reliability."
    assert task.task_type == "research"
    assert task.max_sources == 5


def test_research_task_accepts_custom_values() -> None:
    task = ResearchTask(
        objective="Compare agent evaluation methods.",
        task_type="comparison",
        max_sources=10,
    )

    assert task.objective == "Compare agent evaluation methods."
    assert task.task_type == "comparison"
    assert task.max_sources == 10


def test_research_task_rejects_empty_objective() -> None:
    with pytest.raises(ValidationError):
        ResearchTask(objective="")


def test_research_task_rejects_whitespace_objective() -> None:
    with pytest.raises(ValidationError):
        ResearchTask(objective="   ")


def test_research_task_rejects_invalid_source_limit() -> None:
    with pytest.raises(ValidationError):
        ResearchTask(
            objective="Find evidence about AI agent reliability.",
            max_sources=0,
        )

    with pytest.raises(ValidationError):
        ResearchTask(
            objective="Find evidence about AI agent reliability.",
            max_sources=21,
        )


def test_source_accepts_valid_metadata() -> None:
    retrieved_at = datetime(
        2026,
        8,
        11,
        0,
        0,
        tzinfo=UTC,
    )

    source = Source(
        title="AI Agent Reliability",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at=retrieved_at,
    )

    assert source.title == "AI Agent Reliability"
    assert str(source.url) == "https://example.com/research"
    assert source.publisher == "Example Research"
    assert source.retrieved_at == retrieved_at


def test_source_rejects_empty_metadata() -> None:
    retrieved_at = datetime.now(UTC)

    with pytest.raises(ValidationError):
        Source(
            title="",
            url="https://example.com/research",
            publisher="Example Research",
            retrieved_at=retrieved_at,
        )

    with pytest.raises(ValidationError):
        Source(
            title="AI Agent Reliability",
            url="https://example.com/research",
            publisher="",
            retrieved_at=retrieved_at,
        )


def test_source_rejects_invalid_url() -> None:
    with pytest.raises(ValidationError):
        Source(
            title="AI Agent Reliability",
            url="not-a-url",
            publisher="Example Research",
            retrieved_at=datetime.now(UTC),
        )


def test_source_rejects_naive_datetime() -> None:
    with pytest.raises(ValidationError):
        Source(
            title="AI Agent Reliability",
            url="https://example.com/research",
            publisher="Example Research",
            retrieved_at=datetime(2026, 8, 11, 0, 0),
        )


def test_evidence_accepts_valid_data() -> None:
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

    assert evidence.source == source
    assert (
        evidence.excerpt
        == "Agent reliability remains an important deployment challenge."
    )
    assert evidence.relevance == 0.92


def test_evidence_rejects_empty_excerpt() -> None:
    source = Source(
        title="AI Agent Reliability",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at=datetime.now(UTC),
    )

    with pytest.raises(ValidationError):
        Evidence(
            source=source,
            excerpt="",
            relevance=0.92,
        )

    with pytest.raises(ValidationError):
        Evidence(
            source=source,
            excerpt="   ",
            relevance=0.92,
        )


def test_evidence_rejects_invalid_relevance() -> None:
    source = Source(
        title="AI Agent Reliability",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at=datetime.now(UTC),
    )

    with pytest.raises(ValidationError):
        Evidence(
            source=source,
            excerpt="Relevant evidence.",
            relevance=-0.1,
        )

    with pytest.raises(ValidationError):
        Evidence(
            source=source,
            excerpt="Relevant evidence.",
            relevance=1.1,
        )


def test_evidence_rejects_invalid_source() -> None:
    with pytest.raises(ValidationError):
        Evidence(
            source={
                "title": "AI Agent Reliability",
                "url": "not-a-valid-url",
                "publisher": "Example Research",
                "retrieved_at": datetime.now(UTC),
            },
            excerpt="Relevant evidence.",
            relevance=0.92,
        )


def test_claim_accepts_valid_data() -> None:
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

    assert claim.statement == "Agent reliability remains a deployment challenge."
    assert claim.evidence == [evidence]


def test_claim_rejects_empty_statement() -> None:
    source = Source(
        title="AI Agent Reliability",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at=datetime.now(UTC),
    )

    evidence = Evidence(
        source=source,
        excerpt="Relevant evidence.",
        relevance=0.92,
    )

    with pytest.raises(ValidationError):
        Claim(
            statement="",
            evidence=[evidence],
        )

    with pytest.raises(ValidationError):
        Claim(
            statement="   ",
            evidence=[evidence],
        )


def test_claim_rejects_missing_evidence() -> None:
    with pytest.raises(ValidationError):
        Claim(
            statement="Agent reliability remains a deployment challenge.",
            evidence=[],
        )


def test_research_result_accepts_valid_data() -> None:
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

    result = ResearchResult(
        question="What are the main challenges of AI agent reliability?",
        claims=[claim],
        sources=[source],
    )

    assert result.question == "What are the main challenges of AI agent reliability?"
    assert result.claims == [claim]
    assert result.sources == [source]


def test_research_result_rejects_empty_question() -> None:
    source = Source(
        title="AI Agent Reliability",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at=datetime.now(UTC),
    )

    evidence = Evidence(
        source=source,
        excerpt="Relevant evidence.",
        relevance=0.92,
    )

    claim = Claim(
        statement="Agent reliability remains a deployment challenge.",
        evidence=[evidence],
    )

    with pytest.raises(ValidationError):
        ResearchResult(
            question="",
            claims=[claim],
            sources=[source],
        )

    with pytest.raises(ValidationError):
        ResearchResult(
            question="   ",
            claims=[claim],
            sources=[source],
        )


def test_research_result_rejects_missing_claims() -> None:
    source = Source(
        title="AI Agent Reliability",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at=datetime.now(UTC),
    )

    with pytest.raises(ValidationError):
        ResearchResult(
            question="What are the main challenges of AI agent reliability?",
            claims=[],
            sources=[source],
        )


def test_research_result_rejects_missing_sources() -> None:
    source = Source(
        title="AI Agent Reliability",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at=datetime.now(UTC),
    )

    evidence = Evidence(
        source=source,
        excerpt="Relevant evidence.",
        relevance=0.92,
    )

    claim = Claim(
        statement="Agent reliability remains a deployment challenge.",
        evidence=[evidence],
    )

    with pytest.raises(ValidationError):
        ResearchResult(
            question="What are the main challenges of AI agent reliability?",
            claims=[claim],
            sources=[],
        )
