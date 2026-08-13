from datetime import UTC, datetime

import pytest

from app.application.evaluation.semantic import SemanticQualityEvaluator
from app.domain.evaluation.benchmark import (
    BenchmarkCase,
    BenchmarkEvaluationInput,
)
from app.domain.research.models import (
    Claim,
    Evidence,
    ResearchResult,
    Source,
)


def make_result() -> ResearchResult:
    source_one = Source(
        title="Reliability Source",
        url="https://example.com/reliability",
        publisher="Example Research",
        retrieved_at=datetime(
            2026,
            8,
            13,
            16,
            0,
            tzinfo=UTC,
        ),
    )

    source_two = Source(
        title="Verification Source",
        url="https://example.org/verification",
        publisher="Example Evaluation",
        retrieved_at=datetime(
            2026,
            8,
            13,
            16,
            0,
            tzinfo=UTC,
        ),
    )

    evidence_one = Evidence(
        source=source_one,
        excerpt="Specialized agents can improve reliability.",
        relevance=0.9,
    )

    evidence_two = Evidence(
        source=source_two,
        excerpt="Independent verification reduces unsupported claims.",
        relevance=0.85,
    )

    return ResearchResult(
        question="How do agents improve research reliability?",
        claims=[
            Claim(
                statement=(
                    "Specialized agents improve reliability through focused roles."
                ),
                evidence=[evidence_one],
            ),
            Claim(
                statement=("Independent verification reduces unsupported claims."),
                evidence=[evidence_two],
            ),
        ],
        sources=[
            source_one,
            source_two,
        ],
        execution=None,
    )


def make_case() -> BenchmarkCase:
    return BenchmarkCase(
        id="semantic-test",
        question="How do agents improve research reliability?",
        expected_focus=[
            "specialized agents",
            "verification",
        ],
    )


def make_input() -> BenchmarkEvaluationInput:
    return BenchmarkEvaluationInput(
        case=make_case(),
        result=make_result(),
        multi_agent_results=[],
    )


def test_semantic_evaluator_returns_metrics() -> None:
    evaluator = SemanticQualityEvaluator()

    result = evaluator.evaluate(
        make_input(),
    )

    metric_names = {metric.name for metric in result.metrics}

    assert metric_names == {
        "focus_coverage",
        "claim_source_diversity",
        "evidence_breadth",
        "synthesis_quality",
    }

    assert 0.0 <= result.overall_score <= 1.0


def test_semantic_evaluator_calculates_focus_coverage() -> None:
    evaluator = SemanticQualityEvaluator()

    result = evaluator.evaluate(
        make_input(),
    )

    metric = next(
        metric for metric in result.metrics if metric.name == "focus_coverage"
    )

    assert metric.value == pytest.approx(1.0)


def test_semantic_evaluator_calculates_evidence_breadth() -> None:
    evaluator = SemanticQualityEvaluator()

    result = evaluator.evaluate(
        make_input(),
    )

    metric = next(
        metric for metric in result.metrics if metric.name == "evidence_breadth"
    )

    assert metric.value == pytest.approx(2 / 3)


def test_semantic_evaluator_rejects_question_mismatch() -> None:
    evaluator = SemanticQualityEvaluator()

    case = make_case()
    research_result = make_result()
    research_result.question = "Different question."

    evaluation_input = BenchmarkEvaluationInput(
        case=case,
        result=research_result,
        multi_agent_results=[],
    )

    with pytest.raises(
        ValueError,
        match="question does not match",
    ):
        evaluator.evaluate(
            evaluation_input,
        )


def test_semantic_evaluator_rejects_no_claims() -> None:
    evaluator = SemanticQualityEvaluator()

    research_result = make_result()
    research_result.claims = []

    evaluation_input = BenchmarkEvaluationInput(
        case=make_case(),
        result=research_result,
        multi_agent_results=[],
    )

    with pytest.raises(
        ValueError,
        match="no claims",
    ):
        evaluator.evaluate(
            evaluation_input,
        )


def test_semantic_evaluator_rejects_no_sources() -> None:
    evaluator = SemanticQualityEvaluator()

    research_result = make_result()
    research_result.sources = []

    evaluation_input = BenchmarkEvaluationInput(
        case=make_case(),
        result=research_result,
        multi_agent_results=[],
    )

    with pytest.raises(
        ValueError,
        match="no sources",
    ):
        evaluator.evaluate(
            evaluation_input,
        )
