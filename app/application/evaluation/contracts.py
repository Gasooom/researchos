"""Contracts for ResearchOS evaluation components."""

from typing import Protocol

from app.domain.evaluation.models import EvaluationResult
from app.domain.research.models import ResearchResult


class ResearchEvaluator(Protocol):
    """Contract implemented by research evaluators."""

    def evaluate(
        self,
        result: ResearchResult,
    ) -> EvaluationResult:
        """Evaluate the quality of a research result."""
        ...
