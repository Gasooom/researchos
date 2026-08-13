"""Unified evaluation reporting for ResearchOS."""

from app.application.evaluation.execution import (
    ExecutionQualityEvaluator,
)
from app.application.evaluation.llm_judge import LLMJudgeEvaluator
from app.application.evaluation.research import UnifiedResearchEvaluator
from app.domain.evaluation.models import EvaluationMetric, EvaluationResult
from app.domain.research.models import ResearchResult


class EvaluationReportBuilder:
    """Combine deterministic and LLM-based evaluation into one report."""

    def __init__(
        self,
        research_evaluator: UnifiedResearchEvaluator,
        execution_evaluator: ExecutionQualityEvaluator,
        llm_judge: LLMJudgeEvaluator | None = None,
    ) -> None:
        self.research_evaluator = research_evaluator
        self.execution_evaluator = execution_evaluator
        self.llm_judge = llm_judge

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

        deterministic_score = (
            research_quality.overall_score + execution_quality.overall_score
        ) / 2

        metrics.append(
            EvaluationMetric(
                name="overall_system_quality",
                value=deterministic_score,
                description=(
                    "Combined deterministic score across research "
                    "and execution quality."
                ),
            )
        )

        overall_score = deterministic_score

        if self.llm_judge is not None:
            judge_result = self.llm_judge.evaluate(result)

            metrics.extend(judge_result.metrics)

            metrics.append(
                EvaluationMetric(
                    name="llm_judge_adjusted_quality",
                    value=judge_result.overall_score,
                    description=(
                        "Semantic quality score produced by the configured LLM judge."
                    ),
                )
            )

        return EvaluationResult(
            metrics=metrics,
            overall_score=overall_score,
        )
