"""Core domain models for ResearchOS."""

from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator

from app.core.models.run import ResearchRunOutcome


class ResearchRequest(BaseModel):
    """A user's request for a research task."""

    question: str = Field(min_length=1)
    max_sources: int = Field(default=10, ge=1, le=50)
    depth: str = Field(default="standard")

    @field_validator("question", "depth")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        """Reject values that contain only whitespace."""
        value = value.strip()

        if not value:
            raise ValueError("value must not be empty")

        return value


class ResearchTask(BaseModel):
    """One focused piece of work within a research request."""

    objective: str = Field(min_length=1)
    task_type: str = Field(default="research")
    max_sources: int = Field(default=5, ge=1, le=20)

    @field_validator("objective", "task_type")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        """Reject values that contain only whitespace."""
        value = value.strip()

        if not value:
            raise ValueError("value must not be empty")

        return value


class Source(BaseModel):
    """A source used to support research evidence."""

    title: str = Field(min_length=1)
    url: AnyHttpUrl
    publisher: str = Field(min_length=1)
    retrieved_at: datetime

    @field_validator("title", "publisher")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        """Reject values that contain only whitespace."""
        value = value.strip()

        if not value:
            raise ValueError("value must not be empty")

        return value

    @field_validator("retrieved_at")
    @classmethod
    def validate_timezone(cls, value: datetime) -> datetime:
        """Require timestamps to include timezone information."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("retrieved_at must be timezone-aware")

        return value


class Evidence(BaseModel):
    """A relevant passage extracted from a research source."""

    source: Source
    excerpt: str = Field(min_length=1)
    relevance: float = Field(ge=0.0, le=1.0)

    @field_validator("excerpt")
    @classmethod
    def validate_excerpt(cls, value: str) -> str:
        """Reject excerpts that contain only whitespace."""
        value = value.strip()

        if not value:
            raise ValueError("excerpt must not be empty")

        return value


class Claim(BaseModel):
    """A research statement supported by one or more evidence items."""

    statement: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @field_validator("statement")
    @classmethod
    def validate_statement(cls, value: str) -> str:
        """Reject statements that contain only whitespace."""
        value = value.strip()

        if not value:
            raise ValueError("statement must not be empty")

        return value


class ResearchResult(BaseModel):
    """The structured result produced by a research run."""

    question: str = Field(min_length=1)
    claims: list[Claim] = Field(min_length=1)
    sources: list[Source] = Field(min_length=1)
    execution: ResearchRunOutcome | None = None

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        """Reject questions that contain only whitespace."""
        value = value.strip()

        if not value:
            raise ValueError("question must not be empty")

        return value
