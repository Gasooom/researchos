"""Evidence and claim quality evaluation for ResearchOS."""

from app.core.models.evaluation import EvaluationMetric, EvaluationResult
from app.core.models.research import ResearchResult


class ClaimQualityEvaluator:
    """Evaluate evidence coverage and claim support quality."""

    def evaluate(self, result: ResearchResult) -> EvaluationResult:
        """Compute deterministic claim-quality metrics."""
        if not result.claims:
            raise ValueError("research result contains no claims")

        total_claims = len(result.claims)

        evidence_backed_claims = sum(bool(claim.evidence) for claim in result.claims)

        supported_claims = sum(
            any(evidence.relevance >= 0.8 for evidence in claim.evidence)
            for claim in result.claims
        )

        evidence_coverage = evidence_backed_claims / total_claims
        claim_support_rate = supported_claims / total_claims
        unsupported_claim_rate = 1.0 - claim_support_rate

        metrics = [
            EvaluationMetric(
                name="evidence_coverage",
                value=evidence_coverage,
                description=(
                    "Fraction of claims that contain at least one evidence item."
                ),
            ),
            EvaluationMetric(
                name="claim_support_rate",
                value=claim_support_rate,
                description=(
                    "Fraction of claims with at least one highly "
                    "relevant evidence item."
                ),
            ),
            EvaluationMetric(
                name="unsupported_claim_rate",
                value=unsupported_claim_rate,
                description=(
                    "Fraction of claims without sufficiently relevant "
                    "supporting evidence."
                ),
            ),
        ]

        overall_score = (evidence_coverage + claim_support_rate) / 2

        return EvaluationResult(
            metrics=metrics,
            overall_score=overall_score,
        )
