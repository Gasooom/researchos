"""Verification domain models for ResearchOS."""

from enum import StrEnum

from pydantic import BaseModel, Field


class SourceVerificationStatus(StrEnum):
    """Verification outcome for a research source."""

    VERIFIED = "verified"
    REJECTED = "rejected"


class SourceVerification(BaseModel):
    """Structured verification result for a source."""

    status: SourceVerificationStatus
    reasons: list[str] = Field(min_length=1)


class ClaimVerificationStatus(StrEnum):
    """Verification outcome for a research claim."""

    SUPPORTED = "supported"
    WEAK = "weak"
    UNSUPPORTED = "unsupported"


class ClaimVerification(BaseModel):
    """Structured verification result for a research claim."""

    status: ClaimVerificationStatus
    confidence: float = Field(ge=0.0, le=1.0)
    matched_evidence_count: int = Field(ge=0)
    best_overlap: float = Field(ge=0.0, le=1.0)
    best_relevance: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(min_length=1)
