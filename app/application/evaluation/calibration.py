"""Human calibration services for ResearchOS."""

from datetime import UTC, datetime

from app.domain.evaluation.calibration import (
    CalibrationLabel,
    CalibrationRecord,
)
from app.domain.evaluation.models import EvaluationResult


class HumanCalibrationService:
    """Compare human judgments with LLM evaluation."""

    def calibrate(
        self,
        llm_result: EvaluationResult,
        human: CalibrationLabel,
    ) -> CalibrationRecord:
        """Create a calibration record from an LLM and human evaluation."""
        return CalibrationRecord(
            llm_groundedness=self._metric_value(
                llm_result,
                "llm_groundedness",
            ),
            llm_completeness=self._metric_value(
                llm_result,
                "llm_completeness",
            ),
            llm_uncertainty_handling=self._metric_value(
                llm_result,
                "llm_uncertainty_handling",
            ),
            llm_overall_score=self._metric_value(
                llm_result,
                "llm_judge_overall",
            ),
            human=human,
            created_at=datetime.now(UTC),
        )

    @staticmethod
    def _metric_value(
        result: EvaluationResult,
        name: str,
    ) -> float:
        """Read a required judge metric."""
        for metric in result.metrics:
            if metric.name == name:
                return metric.value

        raise ValueError(f"LLM evaluation missing metric: {name}")
