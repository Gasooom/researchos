"""Unified evaluation reporting for ResearchOS."""

from app.application.evaluation.execution import (
    ExecutionQualityEvaluator,
)
from app.application.evaluation.research import UnifiedResearchEvaluator
from app.domain.evaluation.models import EvaluationMetric, EvaluationResult
from app.domain.research.models import ResearchResult


class EvaluationReportBuilder:
    """Combine research and execution evaluation into one report."""

    def __init__(
        self,
        research_evaluator: UnifiedResearchEvaluator,
        execution_evaluator: ExecutionQualityEvaluator,
    ) -> None:
        self.research_evaluator = research_evaluator
        self.execution_evaluator = execution_evaluator

    def build(self, result: ResearchResult) -> EvaluationResult:
        """Build a unified evaluation report."""
        if result.execution is None:
            raise ValueError("research result has no execution outcome")

        research_quality = self.research_evaluator.evaluate(result)
        execution_quality = self.execution_evaluator.evaluate(
            result.execution,
        )

        metrics = [
            *research_quality.metrics,
            *execution_quality.metrics,
        ]

        overall_score = (
            research_quality.overall_score + execution_quality.overall_score
        ) / 2

        metrics.append(
            EvaluationMetric(
                name="overall_system_quality",
                value=overall_score,
                description=("Combined score across research and execution quality."),
            )
        )

        return EvaluationResult(
            metrics=metrics,
            overall_score=overall_score,
        )
