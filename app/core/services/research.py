"""Research composition services for ResearchOS."""

from app.core.models.research import (
    Claim,
    ResearchRequest,
    ResearchResult,
    Source,
)
from app.core.models.run import ResearchRunOutcome


def build_research_result(
    request: ResearchRequest,
    claims: list[Claim],
    sources: list[Source],
    execution: ResearchRunOutcome | None = None,
) -> ResearchResult:
    """Compose validated research artifacts into a research result."""
    return ResearchResult(
        question=request.question,
        claims=claims,
        sources=sources,
        execution=execution,
    )
