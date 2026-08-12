from datetime import UTC, datetime

import pytest

from app.application.evaluation.retrieval import RetrievalQualityEvaluator
from app.domain.research.models import Claim, Evidence, ResearchResult, Source


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


def make_result(evidence: list[Evidence]) -> ResearchResult:
    claim = Claim(
        statement="Research finding.",
        evidence=evidence,
    )

    return ResearchResult(
        question="What improves AI agent reliability?",
        claims=[claim],
        sources=[item.source for item in evidence],
    )


def test_retrieval_evaluator_calculates_average_relevance() -> None:
    evaluator = RetrievalQualityEvaluator()

    result = make_result(
        [
            make_evidence("High relevance.", 0.9),
            make_evidence("Medium relevance.", 0.7),
        ]
    )

    evaluation = evaluator.evaluate(result)

    assert evaluation.overall_score == pytest.approx(0.8)

    metrics = {metric.name: metric.value for metric in evaluation.metrics}

    assert metrics["average_relevance"] == pytest.approx(0.8)


def test_retrieval_evaluator_calculates_high_relevance_rate() -> None:
    evaluator = RetrievalQualityEvaluator()

    result = make_result(
        [
            make_evidence("High one.", 0.95),
            make_evidence("High two.", 0.85),
            make_evidence("Low one.", 0.6),
        ]
    )

    evaluation = evaluator.evaluate(result)

    metrics = {metric.name: metric.value for metric in evaluation.metrics}

    assert metrics["high_relevance_rate"] == pytest.approx(2 / 3)


def test_retrieval_evaluator_supports_perfect_retrieval() -> None:
    evaluator = RetrievalQualityEvaluator()

    result = make_result(
        [
            make_evidence("Excellent evidence one.", 1.0),
            make_evidence("Excellent evidence two.", 1.0),
        ]
    )

    evaluation = evaluator.evaluate(result)

    assert evaluation.overall_score == pytest.approx(1.0)

    metrics = {metric.name: metric.value for metric in evaluation.metrics}

    assert metrics["high_relevance_rate"] == pytest.approx(1.0)


def test_retrieval_evaluator_supports_low_quality_retrieval() -> None:
    evaluator = RetrievalQualityEvaluator()

    result = make_result(
        [
            make_evidence("Weak evidence one.", 0.2),
            make_evidence("Weak evidence two.", 0.4),
        ]
    )

    evaluation = evaluator.evaluate(result)

    assert evaluation.overall_score == pytest.approx(0.3)

    metrics = {metric.name: metric.value for metric in evaluation.metrics}

    assert metrics["high_relevance_rate"] == pytest.approx(0.0)
