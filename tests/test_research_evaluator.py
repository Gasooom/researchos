from datetime import UTC, datetime

import pytest

from app.core.models.research import Claim, Evidence, ResearchResult, Source
from app.core.services.claim_quality_evaluator import ClaimQualityEvaluator
from app.core.services.research_evaluator import UnifiedResearchEvaluator
from app.core.services.retrieval_evaluator import RetrievalQualityEvaluator


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
    first_evidence = make_evidence(
        "Strong evidence.",
        0.9,
    )
    second_evidence = make_evidence(
        "Weak evidence.",
        0.5,
    )

    return ResearchResult(
        question="What improves AI agent reliability?",
        claims=[
            Claim(
                statement="Strongly supported claim.",
                evidence=[first_evidence],
            ),
            Claim(
                statement="Weakly supported claim.",
                evidence=[second_evidence],
            ),
        ],
        sources=[
            first_evidence.source,
            second_evidence.source,
        ],
    )


def build_evaluator() -> UnifiedResearchEvaluator:
    return UnifiedResearchEvaluator(
        retrieval_evaluator=RetrievalQualityEvaluator(),
        claim_quality_evaluator=ClaimQualityEvaluator(),
    )


def test_unified_evaluator_combines_metrics() -> None:
    evaluator = build_evaluator()

    result = evaluator.evaluate(make_result())

    metric_names = {metric.name for metric in result.metrics}

    assert "average_relevance" in metric_names
    assert "high_relevance_rate" in metric_names
    assert "evidence_coverage" in metric_names
    assert "claim_support_rate" in metric_names
    assert "unsupported_claim_rate" in metric_names
    assert "overall_research_quality" in metric_names


def test_unified_evaluator_combines_scores() -> None:
    evaluator = build_evaluator()

    result = evaluator.evaluate(make_result())

    # Retrieval score:
    # (0.9 + 0.5) / 2 = 0.7
    #
    # Claim score:
    # evidence coverage = 1.0
    # support rate = 0.5
    # claim score = 0.75
    #
    # Overall:
    # (0.7 + 0.75) / 2 = 0.725
    assert result.overall_score == pytest.approx(0.725)


def test_unified_evaluator_exposes_overall_metric() -> None:
    evaluator = build_evaluator()

    result = evaluator.evaluate(make_result())

    overall_metric = next(
        metric for metric in result.metrics if metric.name == "overall_research_quality"
    )

    assert overall_metric.value == pytest.approx(result.overall_score)
