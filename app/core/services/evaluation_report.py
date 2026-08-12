"""Unified evaluation reporting for ResearchOS."""

from app.core.models.evaluation import EvaluationMetric, EvaluationResult
from app.core.models.research import ResearchResult
from app.core.services.execution_quality_evaluator import (
    ExecutionQualityEvaluator,
)
from app.core.services.research_evaluator import UnifiedResearchEvaluator


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
