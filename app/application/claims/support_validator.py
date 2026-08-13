"""Claim support validation services for ResearchOS."""

import re

from app.domain.research.models import Claim
from app.domain.research.verification import (
    ClaimVerification,
    ClaimVerificationStatus,
)


class ClaimSupportValidator:
    """Validate whether a claim is sufficiently supported by its evidence."""

    def __init__(
        self,
        minimum_relevance: float = 0.7,
        supported_overlap: float = 0.6,
        weak_overlap: float = 0.3,
    ) -> None:
        if not 0.0 <= minimum_relevance <= 1.0:
            raise ValueError("minimum_relevance must be between 0 and 1")

        if not 0.0 <= weak_overlap <= 1.0:
            raise ValueError("weak_overlap must be between 0 and 1")

        if not 0.0 <= supported_overlap <= 1.0:
            raise ValueError("supported_overlap must be between 0 and 1")

        if weak_overlap > supported_overlap:
            raise ValueError("weak_overlap must not exceed supported_overlap")

        self.minimum_relevance = minimum_relevance
        self.supported_overlap = supported_overlap
        self.weak_overlap = weak_overlap

    def is_supported(self, claim: Claim) -> bool:
        """Return whether at least one evidence item is sufficiently supportive."""
        verification = self.verify(claim)

        return verification.status == ClaimVerificationStatus.SUPPORTED

    def verify(self, claim: Claim) -> ClaimVerification:
        """Verify a claim against its available evidence."""
        if not claim.evidence:
            return ClaimVerification(
                status=ClaimVerificationStatus.UNSUPPORTED,
                confidence=0.0,
                matched_evidence_count=0,
                best_overlap=0.0,
                best_relevance=0.0,
                reasons=[
                    "claim has no supporting evidence",
                ],
            )

        claim_tokens = self._token_set(claim.statement)

        if not claim_tokens:
            return ClaimVerification(
                status=ClaimVerificationStatus.UNSUPPORTED,
                confidence=0.0,
                matched_evidence_count=0,
                best_overlap=0.0,
                best_relevance=0.0,
                reasons=[
                    "claim contains no meaningful tokens",
                ],
            )

        overlaps: list[tuple[float, float]] = []

        for evidence in claim.evidence:
            evidence_tokens = self._token_set(
                evidence.excerpt,
            )

            if not evidence_tokens:
                overlaps.append(
                    (
                        0.0,
                        evidence.relevance,
                    )
                )
                continue

            overlap = len(claim_tokens & evidence_tokens) / len(claim_tokens)

            overlaps.append(
                (
                    min(overlap, 1.0),
                    evidence.relevance,
                )
            )

        best_overlap, best_relevance = max(
            overlaps,
            key=lambda item: (
                item[0],
                item[1],
            ),
        )

        matched_evidence_count = sum(
            overlap >= self.weak_overlap and relevance >= self.minimum_relevance
            for overlap, relevance in overlaps
        )

        if (
            best_overlap >= self.supported_overlap
            and best_relevance >= self.minimum_relevance
        ):
            confidence = (best_overlap + best_relevance) / 2

            return ClaimVerification(
                status=ClaimVerificationStatus.SUPPORTED,
                confidence=confidence,
                matched_evidence_count=matched_evidence_count,
                best_overlap=best_overlap,
                best_relevance=best_relevance,
                reasons=[
                    "claim wording is substantially supported by relevant evidence",
                ],
            )

        if best_overlap >= self.weak_overlap and best_relevance >= 0.5:
            confidence = (best_overlap + best_relevance) / 2

            return ClaimVerification(
                status=ClaimVerificationStatus.WEAK,
                confidence=confidence,
                matched_evidence_count=matched_evidence_count,
                best_overlap=best_overlap,
                best_relevance=best_relevance,
                reasons=[
                    "evidence is relevant but does not strongly "
                    "support the complete claim",
                ],
            )

        confidence = (best_overlap + best_relevance) / 2

        return ClaimVerification(
            status=ClaimVerificationStatus.UNSUPPORTED,
            confidence=confidence,
            matched_evidence_count=matched_evidence_count,
            best_overlap=best_overlap,
            best_relevance=best_relevance,
            reasons=[
                "available evidence does not sufficiently support the claim",
            ],
        )

    @staticmethod
    def _token_set(text: str) -> set[str]:
        """Normalize text into meaningful tokens."""
        return {
            token
            for token in re.findall(
                r"\w+",
                text.lower(),
            )
            if len(token) > 2
        }
