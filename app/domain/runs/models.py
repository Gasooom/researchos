"""Research run execution models for ResearchOS."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ResearchRunStatus(StrEnum):
    """Execution status for a research run."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ResearchRunFailure(BaseModel):
    """A recorded failure from a research task."""

    task_objective: str = Field(min_length=1)
    error_type: str = Field(min_length=1)
    message: str = Field(min_length=1)


class ResearchRunOutcome(BaseModel):
    """Structured outcome of a research run."""

    status: ResearchRunStatus
    completed_tasks: int = Field(ge=0)
    failed_tasks: int = Field(ge=0)
    failures: list[ResearchRunFailure] = Field(default_factory=list)
    evidence: list[Any] = Field(default_factory=list)
