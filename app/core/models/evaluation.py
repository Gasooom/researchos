"""Evaluation domain models for ResearchOS."""

from pydantic import BaseModel, Field


class EvaluationMetric(BaseModel):
    """A single measurable evaluation metric."""

    name: str = Field(min_length=1)
    value: float
    description: str = Field(min_length=1)


class EvaluationResult(BaseModel):
    """Structured evaluation output for a research run."""

    metrics: list[EvaluationMetric] = Field(min_length=1)
    overall_score: float = Field(ge=0.0, le=1.0)
