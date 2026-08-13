"""Source verification models for ResearchOS."""

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
