from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from app.application.memory.research_memory import (
    ResearchMemoryService,
)
from app.domain.research.memory import ResearchMemoryItem
from app.domain.research.memory_repository import (
    ResearchMemoryRepository,
)
from app.domain.research.models import (
    Claim,
    Evidence,
    ResearchResult,
    Source,
)


def make_result() -> ResearchResult:
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
        excerpt="Evaluation improves research reliability.",
        relevance=0.9,
    )

    claim = Claim(
        statement="Evaluation improves research reliability.",
        evidence=[evidence],
    )

    return ResearchResult(
        question="How can research become more reliable?",
        claims=[claim],
        sources=[source],
        execution=None,
    )


def test_memory_service_retrieves_relevant_memory() -> None:
    repository = Mock(spec=ResearchMemoryRepository)
    repository.search.return_value = [
        ResearchMemoryItem(
            question="How can research become more reliable?",
            summary="Evaluation improves research reliability.",
            claims=make_result().claims,
            evidence=make_result().claims[0].evidence,
            created_at=datetime(
                2026,
                8,
                13,
                11,
                0,
                tzinfo=UTC,
            ),
        )
    ]

    service = ResearchMemoryService(repository)

    result = service.retrieve(
        question="How can research become more reliable?",
        limit=3,
    )

    assert len(result) == 1
    repository.search.assert_called_once_with(
        query="How can research become more reliable?",
        limit=3,
    )


def test_memory_service_stores_research_result() -> None:
    repository = Mock(spec=ResearchMemoryRepository)

    saved_item = ResearchMemoryItem(
        question="How can research become more reliable?",
        summary="Evaluation improves research reliability.",
        claims=make_result().claims,
        evidence=make_result().claims[0].evidence,
        created_at=datetime(
            2026,
            8,
            13,
            11,
            0,
            tzinfo=UTC,
        ),
    )

    repository.save.return_value = saved_item

    service = ResearchMemoryService(repository)

    result = service.store(make_result())

    assert result == saved_item
    repository.save.assert_called_once()


def test_memory_service_rejects_result_without_claims() -> None:
    repository = Mock(spec=ResearchMemoryRepository)

    service = ResearchMemoryService(repository)

    result = make_result()
    result.claims = []

    with pytest.raises(
        ValueError,
        match="research result must contain claims",
    ):
        service.store(result)


def test_memory_service_rejects_result_without_sources() -> None:
    repository = Mock(spec=ResearchMemoryRepository)

    service = ResearchMemoryService(repository)

    result = make_result()
    result.sources = []

    with pytest.raises(
        ValueError,
        match="research result must contain sources",
    ):
        service.store(result)
