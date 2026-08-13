"""Minimal claim critic for ResearchOS."""

from app.application.claims.conflict_detector import ClaimConflictDetector
from app.application.claims.support_classifier import (
    ClaimSupportClassifier,
    SupportLevel,
)
from app.application.claims.support_validator import ClaimSupportValidator
from app.domain.research.models import Claim
from app.domain.research.verification import ClaimVerificationStatus


class ClaimCritic:
    """Identify obvious claim-quality problems requiring review."""

    def __init__(
        self,
        classifier: ClaimSupportClassifier | None = None,
        validator: ClaimSupportValidator | None = None,
        conflict_detector: ClaimConflictDetector | None = None,
    ) -> None:
        self.classifier = classifier or ClaimSupportClassifier()
        self.validator = validator or ClaimSupportValidator()
        self.conflict_detector = conflict_detector or ClaimConflictDetector()

    def inspect(self, claim: Claim) -> list[str]:
        """Return concise reasons why a claim should be reviewed."""
        issues: list[str] = []

        if self.conflict_detector.has_conflict(claim):
            issues.append("conflicting evidence")

        support_level = self.classifier.classify(claim)
        verification = self.validator.verify(claim)

        if support_level == SupportLevel.UNSUPPORTED:
            issues.append("unsupported claim")
        elif support_level == SupportLevel.WEAK:
            issues.append("weak evidence")

        if verification.status == ClaimVerificationStatus.UNSUPPORTED:
            issues.append("claim/evidence mismatch")
        elif verification.status == ClaimVerificationStatus.WEAK:
            issues.append("weak claim/evidence support")

        return list(dict.fromkeys(issues))

    def has_critical_issue(self, claim: Claim) -> bool:
        """Return whether the claim contains a review-worthy issue."""
        return bool(self.inspect(claim))
