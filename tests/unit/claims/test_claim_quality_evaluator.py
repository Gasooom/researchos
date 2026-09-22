from datetime import UTC, datetime

import pytest

from app.application.evaluation.claims import ClaimQualityEvaluator
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


def make_claim(
    statement: str,
    evidence: list[Evidence],
) -> Claim:
    return Claim(
        statement=statement,
        evidence=evidence,
    )


def make_result(claims: list[Claim]) -> ResearchResult:
    sources = [evidence.source for claim in claims for evidence in claim.evidence]

    return ResearchResult(
        question="What improves AI agent reliability?",
        claims=claims,
        sources=sources,
    )


def test_claim_quality_evaluator_calculates_evidence_coverage() -> None:
    evaluator = ClaimQualityEvaluator()

    result = make_result(
        [
            make_claim(
                "Supported claim.",
                [make_evidence("Strong evidence.", 0.95)],
            ),
            make_claim(
                "Another supported claim.",
                [make_evidence("Medium evidence.", 0.6)],
            ),
        ]
    )

    evaluation = evaluator.evaluate(result)

    metrics = {metric.name: metric.value for metric in evaluation.metrics}

    assert metrics["evidence_coverage"] == pytest.approx(1.0)


def test_claim_quality_evaluator_calculates_relevance_rates() -> None:
    evaluator = ClaimQualityEvaluator()

    result = make_result(
        [
            make_claim(
                "Strongly supported.",
                [make_evidence("Strong evidence.", 0.95)],
            ),
            make_claim(
                "Weakly supported.",
                [make_evidence("Weak evidence.", 0.4)],
            ),
        ]
    )

    evaluation = evaluator.evaluate(result)

    metrics = {metric.name: metric.value for metric in evaluation.metrics}

    assert metrics["high_relevance_claim_rate"] == pytest.approx(0.5)
    assert metrics["low_relevance_claim_rate"] == pytest.approx(0.5)
    assert evaluation.overall_score == pytest.approx(0.75)


def test_relevance_rate_ignores_claim_evidence_wording() -> None:
    """Relevance rates track the retrieval score, never the claim wording."""
    evaluator = ClaimQualityEvaluator()

    result = make_result(
        [
            make_claim(
                "Entirely unrelated wording.",
                [make_evidence("Nothing in common whatsoever.", 0.95)],
            ),
        ]
    )

    metrics = {
        metric.name: metric.value for metric in evaluator.evaluate(result).metrics
    }

    assert metrics["high_relevance_claim_rate"] == pytest.approx(1.0)
    assert metrics["claim_evidence_overlap_rate"] == pytest.approx(0.0)


def test_claim_evidence_overlap_is_tautological_when_statement_is_the_excerpt() -> None:
    """Pins the known weakness: the pipeline builds claims from their evidence.

    ResearchOrchestrator._build_result passes the evidence excerpt as the claim
    statement, so overlap is 1.0 by construction and measures nothing about
    genuine support. If this test ever fails, the pipeline changed and the
    metric became meaningful.
    """
    evaluator = ClaimQualityEvaluator()

    excerpt = "Agent reliability remains an important deployment challenge."

    result = make_result(
        [
            make_claim(
                excerpt,
                [make_evidence(excerpt, 0.95)],
            ),
        ]
    )

    metrics = {
        metric.name: metric.value for metric in evaluator.evaluate(result).metrics
    }

    assert metrics["claim_evidence_overlap_rate"] == pytest.approx(1.0)


def test_claim_quality_evaluator_handles_all_strong_claims() -> None:
    evaluator = ClaimQualityEvaluator()

    result = make_result(
        [
            make_claim(
                "Claim one.",
                [make_evidence("Evidence one.", 0.9)],
            ),
            make_claim(
                "Claim two.",
                [make_evidence("Evidence two.", 0.92)],
            ),
        ]
    )

    evaluation = evaluator.evaluate(result)

    assert evaluation.overall_score == pytest.approx(1.0)


def test_claim_quality_evaluator_rejects_empty_claim_set() -> None:
    evaluator = ClaimQualityEvaluator()

    result = ResearchResult.model_construct(
        question="What improves AI agent reliability?",
        claims=[],
        sources=[],
    )

    with pytest.raises(
        ValueError,
        match="research result contains no claims",
    ):
        evaluator.evaluate(result)
