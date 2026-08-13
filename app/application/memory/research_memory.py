"""Application services for ResearchOS research memory."""

from datetime import UTC, datetime

from app.domain.research.memory import ResearchMemoryItem
from app.domain.research.memory_repository import ResearchMemoryRepository
from app.domain.research.models import ResearchResult


class ResearchMemoryService:
    """Manage reusable research knowledge across runs."""

    def __init__(self, repository: ResearchMemoryRepository) -> None:
        self.repository = repository

    def retrieve(
        self,
        question: str,
        limit: int = 5,
    ) -> list[ResearchMemoryItem]:
        """Retrieve prior research relevant to a question."""
        return self.repository.search(
            query=question,
            limit=limit,
        )

    def store(
        self,
        result: ResearchResult,
    ) -> ResearchMemoryItem:
        """Persist reusable findings from a completed research result."""
        if not result.claims:
            raise ValueError("research result must contain claims")

        if not result.sources:
            raise ValueError("research result must contain sources")

        item = ResearchMemoryItem(
            question=result.question,
            summary=self._build_summary(result),
            claims=result.claims,
            evidence=[
                evidence for claim in result.claims for evidence in claim.evidence
            ],
            created_at=datetime.now(UTC),
        )

        return self.repository.save(item)

    @staticmethod
    def _build_summary(result: ResearchResult) -> str:
        """Build a compact reusable summary from research claims."""
        return " ".join(claim.statement for claim in result.claims)
