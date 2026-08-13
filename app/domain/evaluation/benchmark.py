"""Benchmark domain models for ResearchOS."""

from pydantic import BaseModel, Field

from app.domain.research.models import ResearchResult
from app.domain.research.multi_agent import MultiAgentResearchResult


class BenchmarkCase(BaseModel):
    """One reproducible research benchmark case."""

    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    expected_focus: list[str] = Field(min_length=1)


class BenchmarkEvaluationInput(BaseModel):
    """Artifacts used for benchmark-specific quality evaluation."""

    case: BenchmarkCase
    result: ResearchResult
    multi_agent_results: list[MultiAgentResearchResult] = Field(
        default_factory=list,
    )


class BenchmarkExecutionResult(BaseModel):
    """Artifacts produced while executing one benchmark case."""

    result: ResearchResult
    multi_agent_results: list[MultiAgentResearchResult] = Field(
        default_factory=list,
    )

    @property
    def question(self) -> str:
        """Expose the underlying research question."""
        return self.result.question

    @property
    def claims(self):
        """Expose the underlying research claims."""
        return self.result.claims

    @property
    def sources(self):
        """Expose the underlying research sources."""
        return self.result.sources

    @property
    def execution(self):
        """Expose the underlying execution outcome."""
        return self.result.execution


class BenchmarkSummary(BaseModel):
    """Aggregated evaluation results across multiple research runs."""

    runs_evaluated: int = Field(ge=1)
    average_overall_score: float = Field(ge=0.0, le=1.0)
    average_research_quality: float = Field(ge=0.0, le=1.0)
    average_execution_quality: float = Field(ge=0.0, le=1.0)
    average_semantic_quality: float = Field(ge=0.0, le=1.0)
    failure_rate: float = Field(ge=0.0, le=1.0)
    partial_run_rate: float = Field(ge=0.0, le=1.0)


class BenchmarkComparison(BaseModel):
    """Compare benchmark performance between two systems."""

    baseline: BenchmarkSummary
    researchos: BenchmarkSummary
    overall_score_delta: float
    research_quality_delta: float
    execution_quality_delta: float
    semantic_quality_delta: float
    failure_rate_delta: float
    partial_run_rate_delta: float
