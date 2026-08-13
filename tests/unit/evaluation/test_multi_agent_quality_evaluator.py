from datetime import UTC, datetime

import pytest

from app.application.evaluation.multi_agent import (
    MultiAgentQualityEvaluator,
)
from app.domain.evaluation.models import EvaluationResult
from app.domain.research.models import (
    Claim,
    Evidence,
    ResearchResult,
    Source,
)
from app.domain.runs.models import (
    ResearchRunOutcome,
    ResearchRunStatus,
)


def make_result() -> ResearchResult:
    source_one = Source(
        title="AI Reliability",
        url="https://example.com/reliability",
        publisher="Example Research",
        retrieved_at=datetime.now(UTC),
    )

    source_two = Source(
        title="Agent Evaluation",
        url="https://example.org/evaluation",
        publisher="Research Lab",
        retrieved_at=datetime.now(UTC),
    )

    evidence_one = Evidence(
        source=source_one,
        excerpt="Evaluation improves reliability.",
        relevance=0.9,
    )

    evidence_two = Evidence(
        source=source_two,
        excerpt="Traceable execution improves diagnosis.",
        relevance=0.8,
    )

    claim_one = Claim(
        statement="Evaluation improves AI agent reliability.",
        evidence=[evidence_one],
    )

    claim_two = Claim(
        statement="Traceability helps diagnose failures.",
        evidence=[evidence_two],
    )

    return ResearchResult(
        question="How can AI agent reliability improve?",
        claims=[claim_one, claim_two],
        sources=[source_one, source_two],
        execution=None,
    )


def make_outcome() -> ResearchRunOutcome:
    return ResearchRunOutcome(
        status=ResearchRunStatus.SUCCESS,
        completed_tasks=3,
        failed_tasks=0,
        failures=[],
        evidence=[],
    )


def test_multi_agent_evaluator_returns_result() -> None:
    evaluator = MultiAgentQualityEvaluator()

    result = evaluator.evaluate(
        result=make_result(),
        outcome=make_outcome(),
    )

    assert isinstance(result, EvaluationResult)
    assert result.overall_score == pytest.approx(0.8791666667)
    assert len(result.metrics) == 4


def test_multi_agent_evaluator_computes_task_success_rate() -> None:
    evaluator = MultiAgentQualityEvaluator()

    outcome = ResearchRunOutcome(
        status=ResearchRunStatus.PARTIAL,
        completed_tasks=2,
        failed_tasks=1,
        failures=[],
        evidence=[],
    )

    result = evaluator.evaluate(
        result=make_result(),
        outcome=outcome,
    )

    metric = next(
        metric for metric in result.metrics if metric.name == "task_success_rate"
    )

    assert metric.value == pytest.approx(2 / 3)


def test_multi_agent_evaluator_computes_evidence_relevance() -> None:
    evaluator = MultiAgentQualityEvaluator()

    result = evaluator.evaluate(
        result=make_result(),
        outcome=make_outcome(),
    )

    metric = next(
        metric for metric in result.metrics if metric.name == "evidence_relevance"
    )

    assert metric.value == pytest.approx(0.85)


def test_multi_agent_evaluator_computes_claim_coverage() -> None:
    evaluator = MultiAgentQualityEvaluator()

    result = evaluator.evaluate(
        result=make_result(),
        outcome=make_outcome(),
    )

    metric = next(
        metric for metric in result.metrics if metric.name == "claim_evidence_coverage"
    )

    assert metric.value == pytest.approx(1.0)


def test_multi_agent_evaluator_computes_source_diversity() -> None:
    evaluator = MultiAgentQualityEvaluator()

    result = evaluator.evaluate(
        result=make_result(),
        outcome=make_outcome(),
    )

    metric = next(
        metric for metric in result.metrics if metric.name == "source_diversity"
    )

    assert metric.value == pytest.approx(2 / 3)


def test_multi_agent_evaluator_rejects_empty_claims() -> None:
    evaluator = MultiAgentQualityEvaluator()

    result = make_result()
    result.claims = []

    with pytest.raises(
        ValueError,
        match="research result contains no claims",
    ):
        evaluator.evaluate(
            result=result,
            outcome=make_outcome(),
        )


def test_multi_agent_evaluator_rejects_empty_sources() -> None:
    evaluator = MultiAgentQualityEvaluator()

    result = make_result()
    result.sources = []

    with pytest.raises(
        ValueError,
        match="research result contains no sources",
    ):
        evaluator.evaluate(
            result=result,
            outcome=make_outcome(),
        )


def test_multi_agent_evaluator_rejects_no_tasks() -> None:
    evaluator = MultiAgentQualityEvaluator()

    outcome = ResearchRunOutcome(
        status=ResearchRunStatus.FAILED,
        completed_tasks=0,
        failed_tasks=0,
        failures=[],
        evidence=[],
    )

    with pytest.raises(
        ValueError,
        match="research run contains no tasks",
    ):
        evaluator.evaluate(
            result=make_result(),
            outcome=outcome,
        )
