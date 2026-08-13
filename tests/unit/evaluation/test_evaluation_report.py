from datetime import UTC, datetime

import pytest

from app.application.evaluation.claims import ClaimQualityEvaluator
from app.application.evaluation.execution import (
    ExecutionQualityEvaluator,
)
from app.application.evaluation.llm_judge import LLMJudgeEvaluator
from app.application.evaluation.report import EvaluationReportBuilder
from app.application.evaluation.research import UnifiedResearchEvaluator
from app.application.evaluation.retrieval import RetrievalQualityEvaluator
from app.domain.research.models import Claim, Evidence, ResearchResult, Source
from app.domain.runs.models import ResearchRunOutcome, ResearchRunStatus


def make_evidence(
    excerpt: str,
    relevance: float,
) -> Evidence:
    source = Source(
        title="Example Research",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at=datetime.now(UTC),
    )

    return Evidence(
        source=source,
        excerpt=excerpt,
        relevance=relevance,
    )


def make_result() -> ResearchResult:
    evidence = [
        make_evidence("Strong evidence.", 0.9),
        make_evidence("Moderate evidence.", 0.7),
    ]

    return ResearchResult(
        question="What improves AI agent reliability?",
        claims=[
            Claim(
                statement="Supported claim one.",
                evidence=[evidence[0]],
            ),
            Claim(
                statement="Supported claim two.",
                evidence=[evidence[1]],
            ),
        ],
        sources=[item.source for item in evidence],
        execution=ResearchRunOutcome(
            status=ResearchRunStatus.SUCCESS,
            completed_tasks=2,
            failed_tasks=0,
            failures=[],
        ),
    )


def build_research_evaluator() -> UnifiedResearchEvaluator:
    """Build the deterministic research evaluator."""
    return UnifiedResearchEvaluator(
        retrieval_evaluator=RetrievalQualityEvaluator(),
        claim_quality_evaluator=ClaimQualityEvaluator(),
    )


def build_report_builder(
    llm_judge: LLMJudgeEvaluator | None = None,
) -> EvaluationReportBuilder:
    """Build an evaluation report builder."""
    return EvaluationReportBuilder(
        research_evaluator=build_research_evaluator(),
        execution_evaluator=ExecutionQualityEvaluator(),
        llm_judge=llm_judge,
    )


class StubJudge:
    """Deterministic LLM judge for report tests."""

    def generate(self, prompt: str) -> list[dict[str, str]]:
        return [
            {
                "judgment": (
                    '{"groundedness": 0.95, '
                    '"completeness": 0.85, '
                    '"uncertainty_handling": 0.90, '
                    '"overall_score": 0.90, '
                    '"reasoning": "Strongly supported by the evidence."}'
                ),
            }
        ]


def test_evaluation_report_combines_metrics() -> None:
    builder = build_report_builder()

    report = builder.build(make_result())

    metric_names = {metric.name for metric in report.metrics}

    assert "average_relevance" in metric_names
    assert "claim_support_rate" in metric_names
    assert "task_success_rate" in metric_names
    assert "overall_system_quality" in metric_names


def test_evaluation_report_combines_scores() -> None:
    builder = build_report_builder()

    report = builder.build(make_result())

    # Research score:
    # retrieval = (0.9 + 0.7) / 2 = 0.8
    # evidence coverage = 1.0
    # claim support rate = 0.5
    # claim quality = (1.0 + 0.5) / 2 = 0.75
    # unified research = (0.8 + 0.75) / 2 = 0.775
    #
    # execution score = 1.0
    #
    # deterministic overall = (0.775 + 1.0) / 2 = 0.8875
    assert report.overall_score == pytest.approx(0.8875)


def test_evaluation_report_exposes_overall_metric() -> None:
    builder = build_report_builder()

    report = builder.build(make_result())

    overall_metric = next(
        metric for metric in report.metrics if metric.name == "overall_system_quality"
    )

    assert overall_metric.value == pytest.approx(
        report.overall_score,
    )


def test_evaluation_report_includes_llm_judge_metrics() -> None:
    builder = build_report_builder(
        llm_judge=LLMJudgeEvaluator(StubJudge()),
    )

    report = builder.build(make_result())

    metric_names = {metric.name for metric in report.metrics}

    assert "llm_groundedness" in metric_names
    assert "llm_completeness" in metric_names
    assert "llm_uncertainty_handling" in metric_names
    assert "llm_judge_overall" in metric_names
    assert "llm_judge_adjusted_quality" in metric_names


def test_llm_judge_does_not_replace_deterministic_overall_score() -> None:
    builder = build_report_builder(
        llm_judge=LLMJudgeEvaluator(StubJudge()),
    )

    report = builder.build(make_result())

    assert report.overall_score == pytest.approx(0.8875)

    judge_metric = next(
        metric
        for metric in report.metrics
        if metric.name == "llm_judge_adjusted_quality"
    )

    assert judge_metric.value == pytest.approx(0.90)


def test_evaluation_report_requires_execution_outcome() -> None:
    builder = build_report_builder()

    result = make_result()
    result.execution = None

    with pytest.raises(
        ValueError,
        match="research result has no execution outcome",
    ):
        builder.build(result)


def test_evaluation_report_without_judge_preserves_existing_behavior() -> None:
    builder = build_report_builder()

    report = builder.build(make_result())

    assert not any(metric.name.startswith("llm_") for metric in report.metrics)
