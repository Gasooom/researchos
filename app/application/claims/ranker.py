"""Claim ranking services for ResearchOS."""

from app.domain.research.models import Claim


class ClaimRanker:
    """Rank research claims by evidence strength and corroboration."""

    def __init__(
        self,
        max_claims: int = 6,
    ) -> None:
        if max_claims < 1:
            raise ValueError(
                "max_claims must be at least 1",
            )

        self.max_claims = max_claims

    def rank(
        self,
        claims: list[Claim],
    ) -> list[Claim]:
        """Return the strongest claims first."""
        ranked = sorted(
            claims,
            key=self._score,
            reverse=True,
        )

        return ranked[: self.max_claims]

    def _score(
        self,
        claim: Claim,
    ) -> float:
        """Calculate a deterministic claim-quality score."""
        if not claim.evidence:
            return 0.0

        average_relevance = sum(
            evidence.relevance for evidence in claim.evidence
        ) / len(claim.evidence)

        independent_sources = len(
            {str(evidence.source.url) for evidence in claim.evidence}
        )

        corroboration = (
            min(
                independent_sources,
                3,
            )
            / 3
        )

        return (average_relevance * 0.60) + (corroboration * 0.40)
