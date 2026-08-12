"""Contracts for ResearchOS evaluation components."""

from typing import Protocol

from app.core.models.evaluation import EvaluationResult
from app.core.models.research import ResearchResult


class ResearchEvaluator(Protocol):
    """Contract implemented by research evaluators."""

    def evaluate(
        self,
        result: ResearchResult,
    ) -> EvaluationResult:
        """Evaluate the quality of a research result."""
        ...
