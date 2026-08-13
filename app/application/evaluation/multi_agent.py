"""Multi-agent research quality evaluation for ResearchOS."""

from app.domain.evaluation.models import EvaluationMetric, EvaluationResult
from app.domain.research.models import ResearchResult
from app.domain.runs.models import ResearchRunOutcome


class MultiAgentQualityEvaluator:
    """Evaluate quality characteristics of a multi-agent research result."""

    def evaluate(
        self,
        result: ResearchResult,
        outcome: ResearchRunOutcome,
    ) -> EvaluationResult:
        """Compute deterministic multi-agent quality metrics."""
        if not result.claims:
            raise ValueError("research result contains no claims")

        if not result.sources:
            raise ValueError("research result contains no sources")

        total_tasks = outcome.completed_tasks + outcome.failed_tasks

        if total_tasks == 0:
            raise ValueError("research run contains no tasks")

        task_success_rate = outcome.completed_tasks / total_tasks

        evidence_items = [
            evidence for claim in result.claims for evidence in claim.evidence
        ]

        if not evidence_items:
            raise ValueError("research result contains no evidence")

        average_relevance = sum(item.relevance for item in evidence_items) / len(
            evidence_items
        )

        evidence_coverage = sum(bool(claim.evidence) for claim in result.claims) / len(
            result.claims
        )

        source_count = len(result.sources)
        source_diversity = min(source_count / 3.0, 1.0)

        metrics = [
            EvaluationMetric(
                name="task_success_rate",
                value=task_success_rate,
                description=(
                    "Fraction of planned multi-agent tasks completed successfully."
                ),
            ),
            EvaluationMetric(
                name="evidence_relevance",
                value=average_relevance,
                description=(
                    "Average relevance across evidence supporting the "
                    "multi-agent result."
                ),
            ),
            EvaluationMetric(
                name="claim_evidence_coverage",
                value=evidence_coverage,
                description=(
                    "Fraction of generated claims backed by at least one evidence item."
                ),
            ),
            EvaluationMetric(
                name="source_diversity",
                value=source_diversity,
                description=(
                    "Normalized score reflecting the number of distinct "
                    "sources used by the result."
                ),
            ),
        ]

        overall_score = (
            task_success_rate + average_relevance + evidence_coverage + source_diversity
        ) / 4

        return EvaluationResult(
            metrics=metrics,
            overall_score=overall_score,
        )
