from datetime import UTC, datetime

import pytest

from app.domain.runs.models import ResearchRunOutcome, ResearchRunStatus
from app.domain.runs.observability import RunObservation
from app.domain.runs.record import ResearchRunRecord
from app.infrastructure.persistence.sqlite_run_repository import (
    SQLiteResearchRunRepository,
)


@pytest.fixture(scope="module")
def repository(
    tmp_path_factory: pytest.TempPathFactory,
) -> SQLiteResearchRunRepository:
    """Create one SQLite repository for the integration test module."""
    database_path = tmp_path_factory.mktemp("sqlite") / "researchos.db"

    return SQLiteResearchRunRepository(
        str(database_path),
    )


@pytest.fixture(autouse=True)
def clean_repository(
    repository: SQLiteResearchRunRepository,
) -> None:
    """Clear persisted runs before each test."""
    with repository._connect() as connection:
        connection.execute("DELETE FROM research_runs")
        connection.commit()


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


def make_observed_run() -> ResearchRunRecord:
    return ResearchRunRecord(
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        outcome=ResearchRunOutcome(
            status=ResearchRunStatus.PARTIAL,
            completed_tasks=2,
            failed_tasks=1,
            failures=[],
            evidence=[],
        ),
        observation=RunObservation(
            duration_seconds=1.75,
            total_tasks=3,
            completed_tasks=2,
            failed_tasks=1,
            status=ResearchRunStatus.PARTIAL,
        ),
    )


def test_sqlite_repository_persists_run(
    repository: SQLiteResearchRunRepository,
) -> None:
    run = make_run()

    repository.save(run)

    loaded = repository.get(run.id)

    assert loaded == run


def test_sqlite_repository_persists_across_repository_instances(
    repository: SQLiteResearchRunRepository,
) -> None:
    run = make_run()

    repository.save(run)

    second_repository = SQLiteResearchRunRepository(
        repository.database_path,
    )

    assert second_repository.get(run.id) == run


def test_sqlite_repository_lists_runs(
    repository: SQLiteResearchRunRepository,
) -> None:
    first = make_run()
    second = make_run()

    repository.save(first)
    repository.save(second)

    assert repository.list() == [first, second]


def test_sqlite_repository_updates_existing_run(
    repository: SQLiteResearchRunRepository,
) -> None:
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


def test_sqlite_repository_persists_observation(
    repository: SQLiteResearchRunRepository,
) -> None:
    run = make_observed_run()

    repository.save(run)

    loaded = repository.get(run.id)

    assert loaded == run
    assert loaded is not None
    assert loaded.observation is not None
    assert loaded.observation.duration_seconds == 1.75
    assert loaded.observation.total_tasks == 3
    assert loaded.observation.completed_tasks == 2
    assert loaded.observation.failed_tasks == 1
