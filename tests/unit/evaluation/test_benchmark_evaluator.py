from app.application.evaluation.benchmark import BenchmarkEvaluator
from app.domain.evaluation.models import EvaluationMetric, EvaluationResult
from app.domain.runs.models import ResearchRunOutcome, ResearchRunStatus


def make_report(
    overall_score: float,
    research_quality: float,
    semantic_quality: float,
    task_success_rate: float,
    failure_rate: float,
) -> EvaluationResult:
    return EvaluationResult(
        metrics=[
            EvaluationMetric(
                name="overall_research_quality",
                value=research_quality,
                description="Research quality.",
            ),
            EvaluationMetric(
                name="semantic_quality",
                value=semantic_quality,
                description="Semantic quality.",
            ),
            EvaluationMetric(
                name="task_success_rate",
                value=task_success_rate,
                description="Task success rate.",
            ),
            EvaluationMetric(
                name="failure_rate",
                value=failure_rate,
                description="Failure rate.",
            ),
        ],
        overall_score=overall_score,
    )


def make_outcome(status: ResearchRunStatus) -> ResearchRunOutcome:
    if status == ResearchRunStatus.SUCCESS:
        return ResearchRunOutcome(
            status=status,
            completed_tasks=2,
            failed_tasks=0,
        )

    if status == ResearchRunStatus.PARTIAL:
        return ResearchRunOutcome(
            status=status,
            completed_tasks=1,
            failed_tasks=1,
        )

    return ResearchRunOutcome(
        status=status,
        completed_tasks=0,
        failed_tasks=2,
    )


def test_benchmark_aggregates_multiple_runs() -> None:
    evaluator = BenchmarkEvaluator()

    summary = evaluator.evaluate(
        reports=[
            make_report(
                overall_score=0.9,
                research_quality=0.8,
                semantic_quality=0.75,
                task_success_rate=1.0,
                failure_rate=0.0,
            ),
            make_report(
                overall_score=0.7,
                research_quality=0.6,
                semantic_quality=0.55,
                task_success_rate=0.5,
                failure_rate=0.5,
            ),
        ],
        outcomes=[
            make_outcome(ResearchRunStatus.SUCCESS),
            make_outcome(ResearchRunStatus.PARTIAL),
        ],
    )

    assert summary.runs_evaluated == 2
    assert summary.average_overall_score == 0.8
    assert summary.average_research_quality == 0.7
    assert summary.average_semantic_quality == 0.65

    # Run 1 execution score:
    # 1.0 * (1 - 0.0) = 1.0
    #
    # Run 2 execution score:
    # 0.5 * (1 - 0.5) = 0.25
    #
    # Average execution score:
    # (1.0 + 0.25) / 2 = 0.625
    assert summary.average_execution_quality == 0.625

    assert summary.failure_rate == 0.0
    assert summary.partial_run_rate == 0.5


def test_benchmark_tracks_failed_runs() -> None:
    evaluator = BenchmarkEvaluator()

    summary = evaluator.evaluate(
        reports=[
            make_report(
                overall_score=0.0,
                research_quality=0.0,
                semantic_quality=0.0,
                task_success_rate=0.0,
                failure_rate=1.0,
            ),
            make_report(
                overall_score=1.0,
                research_quality=1.0,
                semantic_quality=1.0,
                task_success_rate=1.0,
                failure_rate=0.0,
            ),
        ],
        outcomes=[
            make_outcome(ResearchRunStatus.FAILED),
            make_outcome(ResearchRunStatus.SUCCESS),
        ],
    )

    assert summary.failure_rate == 0.5
    assert summary.partial_run_rate == 0.0
    assert summary.average_semantic_quality == 0.5


def test_benchmark_rejects_empty_reports() -> None:
    evaluator = BenchmarkEvaluator()

    try:
        evaluator.evaluate(
            reports=[],
            outcomes=[],
        )
    except ValueError as exc:
        assert str(exc) == "benchmark requires at least one report"
    else:
        raise AssertionError("Expected ValueError")


def test_benchmark_requires_matching_lengths() -> None:
    evaluator = BenchmarkEvaluator()

    report = make_report(
        overall_score=0.9,
        research_quality=0.8,
        semantic_quality=0.75,
        task_success_rate=1.0,
        failure_rate=0.0,
    )

    try:
        evaluator.evaluate(
            reports=[report],
            outcomes=[],
        )
    except ValueError as exc:
        assert str(exc) == ("reports and outcomes must have the same length")
    else:
        raise AssertionError("Expected ValueError")
