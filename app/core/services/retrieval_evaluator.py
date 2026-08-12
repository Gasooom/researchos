"""Retrieval quality evaluation for ResearchOS."""

from app.core.models.evaluation import EvaluationMetric, EvaluationResult
from app.core.models.research import ResearchResult


class RetrievalQualityEvaluator:
    """Evaluate retrieval quality using evidence relevance scores."""

    def evaluate(self, result: ResearchResult) -> EvaluationResult:
        """Compute deterministic retrieval quality metrics."""
        evidence = [item for claim in result.claims for item in claim.evidence]

        if not evidence:
            raise ValueError("research result contains no evidence")

        relevance_scores = [evidence_item.relevance for evidence_item in evidence]

        average_relevance = sum(relevance_scores) / len(relevance_scores)

        high_relevance_rate = sum(score >= 0.8 for score in relevance_scores) / len(
            relevance_scores
        )

        return EvaluationResult(
            metrics=[
                EvaluationMetric(
                    name="average_relevance",
                    value=average_relevance,
                    description=("Average relevance score across retrieved evidence."),
                ),
                EvaluationMetric(
                    name="high_relevance_rate",
                    value=high_relevance_rate,
                    description=(
                        "Fraction of evidence items with relevance at or above 0.8."
                    ),
                ),
            ],
            overall_score=average_relevance,
        )
