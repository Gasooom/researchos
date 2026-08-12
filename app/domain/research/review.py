"""Human review domain models for ResearchOS."""

from enum import StrEnum


class ReviewStatus(StrEnum):
    """Lifecycle states for human review."""

    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewDecision(StrEnum):
    """Possible decisions made during human review."""

    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_MORE_EVIDENCE = "request_more_evidence"
