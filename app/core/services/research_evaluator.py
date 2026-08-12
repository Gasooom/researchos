"""Unified research quality evaluation for ResearchOS."""

from app.core.models.evaluation import EvaluationMetric, EvaluationResult
from app.core.models.research import ResearchResult
from app.core.services.claim_quality_evaluator import ClaimQualityEvaluator
from app.core.services.retrieval_evaluator import RetrievalQualityEvaluator


class UnifiedResearchEvaluator:
    """Combine retrieval and claim-quality evaluation."""

    def __init__(
        self,
        retrieval_evaluator: RetrievalQualityEvaluator,
        claim_quality_evaluator: ClaimQualityEvaluator,
    ) -> None:
        self.retrieval_evaluator = retrieval_evaluator
        self.claim_quality_evaluator = claim_quality_evaluator

    def evaluate(self, result: ResearchResult) -> EvaluationResult:
        """Evaluate overall research quality."""
        retrieval = self.retrieval_evaluator.evaluate(result)
        claim_quality = self.claim_quality_evaluator.evaluate(result)

        metrics = [
            *retrieval.metrics,
            *claim_quality.metrics,
        ]

        overall_score = (retrieval.overall_score + claim_quality.overall_score) / 2

        metrics.append(
            EvaluationMetric(
                name="overall_research_quality",
                value=overall_score,
                description=("Combined score across retrieval and claim quality."),
            )
        )

        return EvaluationResult(
            metrics=metrics,
            overall_score=overall_score,
        )
