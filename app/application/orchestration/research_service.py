"""Research composition services for ResearchOS."""

from app.domain.research.models import (
    Claim,
    ResearchRequest,
    ResearchResult,
    Source,
)
from app.domain.runs.models import ResearchRunOutcome


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
