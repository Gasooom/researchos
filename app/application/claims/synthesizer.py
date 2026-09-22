"""Claim construction from synthesized research findings."""

from app.application.claims.grounder import ClaimGrounder
from app.domain.research.models import Claim
from app.domain.research.multi_agent import MultiAgentResearchResult


class SynthesizedClaimBuilder:
    """Build claims from synthesis findings rather than raw evidence excerpts.

    Claim statements come from the synthesis agent, so their wording is produced
    independently of the excerpts kept as their evidence. That independence is
    what turns claim/evidence overlap into a real signal instead of an identity.
    """

    def __init__(self, grounder: ClaimGrounder | None = None) -> None:
        self.grounder = grounder or ClaimGrounder()

    def build(
        self,
        results: list[MultiAgentResearchResult],
    ) -> list[Claim]:
        """Create one claim per synthesized finding, grounded in its evidence."""
        claims: list[Claim] = []

        for result in results:
            for finding in result.synthesis.supporting_points:
                if not finding.strip():
                    continue

                claims.append(
                    self.grounder.ground(
                        statement=finding,
                        evidence=list(result.evidence),
                    )
                )

        return claims
