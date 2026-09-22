"""Evidence and claim quality evaluation for ResearchOS."""

from app.application.claims.support_validator import ClaimSupportValidator
from app.domain.evaluation.models import EvaluationMetric, EvaluationResult
from app.domain.research.models import ResearchResult

RELEVANCE_THRESHOLD = 0.8


class ClaimQualityEvaluator:
    """Evaluate evidence coverage and retrieval-relevance quality."""

    def __init__(
        self,
        support_validator: ClaimSupportValidator | None = None,
    ) -> None:
        self.support_validator = support_validator or ClaimSupportValidator()

    def evaluate(self, result: ResearchResult) -> EvaluationResult:
        """Compute deterministic claim-quality metrics."""
        if not result.claims:
            raise ValueError("research result contains no claims")

        total_claims = len(result.claims)

        evidence_backed_claims = sum(bool(claim.evidence) for claim in result.claims)

        high_relevance_claims = sum(
            any(
                evidence.relevance >= RELEVANCE_THRESHOLD for evidence in claim.evidence
            )
            for claim in result.claims
        )

        overlapping_claims = sum(
            self.support_validator.is_supported(claim) for claim in result.claims
        )

        evidence_coverage = evidence_backed_claims / total_claims
        high_relevance_claim_rate = high_relevance_claims / total_claims
        low_relevance_claim_rate = 1.0 - high_relevance_claim_rate
        claim_evidence_overlap_rate = overlapping_claims / total_claims

        metrics = [
            EvaluationMetric(
                name="evidence_coverage",
                value=evidence_coverage,
                description=(
                    "Fraction of claims that contain at least one evidence item."
                ),
            ),
            EvaluationMetric(
                name="high_relevance_claim_rate",
                value=high_relevance_claim_rate,
                description=(
                    "Fraction of claims whose best evidence scored at or above "
                    f"{RELEVANCE_THRESHOLD} retrieval relevance. This measures "
                    "retrieval confidence, not whether the evidence supports "
                    "the claim."
                ),
            ),
            EvaluationMetric(
                name="low_relevance_claim_rate",
                value=low_relevance_claim_rate,
                description=(
                    "Fraction of claims whose best evidence scored below "
                    f"{RELEVANCE_THRESHOLD} retrieval relevance."
                ),
            ),
            EvaluationMetric(
                name="claim_evidence_overlap_rate",
                value=claim_evidence_overlap_rate,
                description=(
                    "Fraction of claims whose wording overlaps their evidence "
                    "enough to pass ClaimSupportValidator. Reads near 1.0 while "
                    "claims are built verbatim from their evidence excerpts, so "
                    "it currently measures pipeline construction rather than "
                    "genuine support."
                ),
            ),
        ]

        overall_score = (evidence_coverage + high_relevance_claim_rate) / 2

        return EvaluationResult(
            metrics=metrics,
            overall_score=overall_score,
        )
