"""Application services for composing research domain objects."""

from app.core.models.research import (
    Claim,
    ResearchRequest,
    ResearchResult,
    Source,
)


def build_research_result(
    request: ResearchRequest,
    claims: list[Claim],
    sources: list[Source],
) -> ResearchResult:
    """Compose validated research artifacts into a research result."""
    return ResearchResult(
        question=request.question,
        claims=claims,
        sources=sources,
    )
