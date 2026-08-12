"""Benchmark domain models for ResearchOS."""

from pydantic import BaseModel, Field


class BenchmarkSummary(BaseModel):
    """Aggregated evaluation results across multiple research runs."""

    runs_evaluated: int = Field(ge=1)
    average_overall_score: float = Field(ge=0.0, le=1.0)
    average_research_quality: float = Field(ge=0.0, le=1.0)
    average_execution_quality: float = Field(ge=0.0, le=1.0)
    failure_rate: float = Field(ge=0.0, le=1.0)
    partial_run_rate: float = Field(ge=0.0, le=1.0)
