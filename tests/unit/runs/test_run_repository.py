from datetime import UTC, datetime
from uuid import uuid4

from app.domain.runs.models import ResearchRunOutcome, ResearchRunStatus
from app.domain.runs.record import ResearchRunRecord
from app.infrastructure.persistence.in_memory_run_repository import (
    InMemoryResearchRunRepository,
)


def make_run() -> ResearchRunRecord:
    return ResearchRunRecord(
        created_at=datetime.now(UTC),
        outcome=ResearchRunOutcome(
            status=ResearchRunStatus.SUCCESS,
            completed_tasks=2,
            failed_tasks=0,
            failures=[],
            evidence=[],
        ),
    )


def test_repository_saves_and_gets_run() -> None:
    repository = InMemoryResearchRunRepository()
    run = make_run()

    saved = repository.save(run)

    assert saved == run
    assert repository.get(run.id) == run


def test_repository_returns_none_for_unknown_run() -> None:
    repository = InMemoryResearchRunRepository()

    assert repository.get(uuid4()) is None


def test_repository_lists_runs() -> None:
    repository = InMemoryResearchRunRepository()

    first = make_run()
    second = make_run()

    repository.save(first)
    repository.save(second)

    assert repository.list() == [first, second]


def test_repository_replaces_existing_run() -> None:
    repository = InMemoryResearchRunRepository()
    run = make_run()

    repository.save(run)

    updated = run.model_copy(
        update={
            "completed_at": datetime.now(UTC),
            "outcome": ResearchRunOutcome(
                status=ResearchRunStatus.PARTIAL,
                completed_tasks=1,
                failed_tasks=1,
                failures=[],
                evidence=[],
            ),
        }
    )

    repository.save(updated)

    assert repository.get(run.id) == updated
    assert len(repository.list()) == 1
