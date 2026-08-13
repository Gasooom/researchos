"""SQLite research run repository for ResearchOS."""

import json
import sqlite3
from datetime import datetime
from uuid import UUID

from app.domain.runs.models import ResearchRunOutcome
from app.domain.runs.observability import RunObservation
from app.domain.runs.record import ResearchRunRecord


class SQLiteResearchRunRepository:
    """Persist research run records in SQLite."""

    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection with row access by column name."""
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        """Create the run table when it does not already exist."""
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS research_runs (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    outcome_json TEXT NOT NULL,
                    observation_json TEXT
                )
                """
            )

            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(research_runs)"
                ).fetchall()
            }

            if "observation_json" not in columns:
                connection.execute(
                    """
                    ALTER TABLE research_runs
                    ADD COLUMN observation_json TEXT
                    """
                )

            connection.commit()

    def save(self, run: ResearchRunRecord) -> ResearchRunRecord:
        """Persist or replace a research run."""
        observation_json = (
            run.observation.model_dump_json() if run.observation is not None else None
        )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO research_runs
                (
                    id,
                    created_at,
                    completed_at,
                    outcome_json,
                    observation_json
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(run.id),
                    run.created_at.isoformat(),
                    (
                        run.completed_at.isoformat()
                        if run.completed_at is not None
                        else None
                    ),
                    run.outcome.model_dump_json(),
                    observation_json,
                ),
            )
            connection.commit()

        return run

    def get(self, run_id: UUID) -> ResearchRunRecord | None:
        """Return a stored run by identifier."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    created_at,
                    completed_at,
                    outcome_json,
                    observation_json
                FROM research_runs
                WHERE id = ?
                """,
                (str(run_id),),
            ).fetchone()

        if row is None:
            return None

        return self._to_record(row)

    def list(self) -> list[ResearchRunRecord]:
        """Return all stored runs ordered by creation time."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    created_at,
                    completed_at,
                    outcome_json,
                    observation_json
                FROM research_runs
                ORDER BY created_at ASC
                """
            ).fetchall()

        return [self._to_record(row) for row in rows]

    @staticmethod
    def _to_record(row: sqlite3.Row) -> ResearchRunRecord:
        """Convert a database row into a domain run record."""
        observation_json = row["observation_json"]

        return ResearchRunRecord(
            id=UUID(row["id"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"] is not None
                else None
            ),
            outcome=ResearchRunOutcome.model_validate(json.loads(row["outcome_json"])),
            observation=(
                RunObservation.model_validate(json.loads(observation_json))
                if observation_json is not None
                else None
            ),
        )
