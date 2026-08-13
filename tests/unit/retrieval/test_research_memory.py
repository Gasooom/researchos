from datetime import UTC, datetime

import pytest

from app.domain.research.memory import ResearchMemoryItem
from app.domain.research.models import Claim, Evidence, Source
from app.infrastructure.persistence.in_memory_research_memory import (
    InMemoryResearchMemoryRepository,
)


def make_memory(
    question: str,
    summary: str,
) -> ResearchMemoryItem:
    source = Source(
        title="Example Research",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at=datetime(
            2026,
            8,
            13,
            11,
            0,
            tzinfo=UTC,
        ),
    )

    evidence = Evidence(
        source=source,
        excerpt=summary,
        relevance=0.9,
    )

    claim = Claim(
        statement=summary,
        evidence=[evidence],
    )

    return ResearchMemoryItem(
        question=question,
        summary=summary,
        claims=[claim],
        evidence=[evidence],
        created_at=datetime(
            2026,
            8,
            13,
            11,
            0,
            tzinfo=UTC,
        ),
    )


def test_memory_repository_saves_items() -> None:
    repository = InMemoryResearchMemoryRepository()

    item = make_memory(
        "How do AI agents become reliable?",
        "Evaluation improves reliability.",
    )

    saved = repository.save(item)

    assert saved == item


def test_memory_repository_retrieves_relevant_items() -> None:
    repository = InMemoryResearchMemoryRepository()

    reliability = make_memory(
        "How do AI agents become reliable?",
        "Evaluation improves reliability.",
    )

    unrelated = make_memory(
        "How do databases scale?",
        "Indexing improves query performance.",
    )

    repository.save(reliability)
    repository.save(unrelated)

    results = repository.search("AI agent reliability")

    assert results == [reliability]


def test_memory_repository_ranks_more_relevant_items_first() -> None:
    repository = InMemoryResearchMemoryRepository()

    weak = make_memory(
        "AI agents",
        "Agents can use tools.",
    )

    strong = make_memory(
        "AI agent reliability evaluation",
        "Evaluation improves AI agent reliability.",
    )

    repository.save(weak)
    repository.save(strong)

    results = repository.search("AI agent reliability")

    assert results[0] == strong


def test_memory_repository_respects_limit() -> None:
    repository = InMemoryResearchMemoryRepository()

    repository.save(
        make_memory(
            "AI agent reliability",
            "Evaluation improves reliability.",
        )
    )
    repository.save(
        make_memory(
            "AI agent evaluation",
            "Evaluation measures reliability.",
        )
    )

    results = repository.search(
        "AI agent reliability",
        limit=1,
    )

    assert len(results) == 1


def test_memory_repository_rejects_invalid_limit() -> None:
    repository = InMemoryResearchMemoryRepository()

    with pytest.raises(ValueError, match="limit"):
        repository.search("AI agents", limit=0)


def test_memory_repository_returns_empty_for_blank_query() -> None:
    repository = InMemoryResearchMemoryRepository()

    repository.save(
        make_memory(
            "AI agent reliability",
            "Evaluation improves reliability.",
        )
    )

    assert repository.search("   ") == []
