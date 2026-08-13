import pytest

from app.application.evaluation.benchmark import BenchmarkEvaluator
from app.domain.evaluation.benchmark import (
    BenchmarkComparison,
    BenchmarkSummary,
)


def make_summary(
    overall: float,
    research: float,
    execution: float,
    semantic: float,
    failure: float,
    partial: float,
) -> BenchmarkSummary:
    return BenchmarkSummary(
        runs_evaluated=3,
        average_overall_score=overall,
        average_research_quality=research,
        average_execution_quality=execution,
        average_semantic_quality=semantic,
        failure_rate=failure,
        partial_run_rate=partial,
    )


def test_benchmark_comparison_calculates_deltas() -> None:
    evaluator = BenchmarkEvaluator()

    baseline = make_summary(
        overall=0.70,
        research=0.65,
        execution=0.80,
        semantic=0.60,
        failure=0.20,
        partial=0.10,
    )

    researchos = make_summary(
        overall=0.85,
        research=0.82,
        execution=0.94,
        semantic=0.77,
        failure=0.05,
        partial=0.02,
    )

    comparison = evaluator.compare(
        baseline=baseline,
        researchos=researchos,
    )

    assert isinstance(comparison, BenchmarkComparison)
    assert comparison.overall_score_delta == pytest.approx(0.15)
    assert comparison.research_quality_delta == pytest.approx(0.17)
    assert comparison.execution_quality_delta == pytest.approx(0.14)
    assert comparison.semantic_quality_delta == pytest.approx(0.17)
    assert comparison.failure_rate_delta == pytest.approx(-0.15)
    assert comparison.partial_run_rate_delta == pytest.approx(-0.08)


def test_benchmark_comparison_preserves_summaries() -> None:
    evaluator = BenchmarkEvaluator()

    baseline = make_summary(
        overall=0.70,
        research=0.65,
        execution=0.80,
        semantic=0.60,
        failure=0.20,
        partial=0.10,
    )

    researchos = make_summary(
        overall=0.85,
        research=0.82,
        execution=0.94,
        semantic=0.77,
        failure=0.05,
        partial=0.02,
    )

    comparison = evaluator.compare(
        baseline=baseline,
        researchos=researchos,
    )

    assert comparison.baseline == baseline
    assert comparison.researchos == researchos


def test_benchmark_comparison_requires_matching_run_counts() -> None:
    evaluator = BenchmarkEvaluator()

    baseline = BenchmarkSummary(
        runs_evaluated=2,
        average_overall_score=0.7,
        average_research_quality=0.7,
        average_execution_quality=0.7,
        average_semantic_quality=0.6,
        failure_rate=0.1,
        partial_run_rate=0.1,
    )

    researchos = BenchmarkSummary(
        runs_evaluated=3,
        average_overall_score=0.8,
        average_research_quality=0.8,
        average_execution_quality=0.8,
        average_semantic_quality=0.8,
        failure_rate=0.05,
        partial_run_rate=0.05,
    )

    with pytest.raises(
        ValueError,
        match="same number of runs",
    ):
        evaluator.compare(
            baseline=baseline,
            researchos=researchos,
        )
