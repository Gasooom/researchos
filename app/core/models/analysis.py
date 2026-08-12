"""Analysis domain models for ResearchOS."""

from pydantic import BaseModel, Field, field_validator


class AnalysisResult(BaseModel):
    """Structured analytical output derived from evidence."""

    summary: str = Field(min_length=1)
    key_points: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        """Reject summaries that contain only whitespace."""
        value = value.strip()

        if not value:
            raise ValueError("summary must not be empty")

        return value

    @field_validator("key_points")
    @classmethod
    def validate_key_points(cls, value: list[str]) -> list[str]:
        """Reject key points that contain only whitespace."""
        cleaned_points = [point.strip() for point in value]

        if any(not point for point in cleaned_points):
            raise ValueError("key_points must not contain empty values")

        return cleaned_points
