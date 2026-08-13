from datetime import UTC

import pytest

from app.application.evaluation.calibration import (
    HumanCalibrationService,
)
from app.domain.evaluation.calibration import (
    CalibrationLabel,
    CalibrationRecord,
)
from app.domain.evaluation.models import (
    EvaluationMetric,
    EvaluationResult,
)


def make_llm_result() -> EvaluationResult:
    return EvaluationResult(
        metrics=[
            EvaluationMetric(
                name="llm_groundedness",
                value=0.90,
                description="Groundedness.",
            ),
            EvaluationMetric(
                name="llm_completeness",
                value=0.80,
                description="Completeness.",
            ),
            EvaluationMetric(
                name="llm_uncertainty_handling",
                value=0.85,
                description="Uncertainty handling.",
            ),
            EvaluationMetric(
                name="llm_judge_overall",
                value=0.85,
                description="Overall judge score.",
            ),
        ],
        overall_score=0.85,
    )


def make_human_label() -> CalibrationLabel:
    return CalibrationLabel(
        groundedness=0.95,
        completeness=0.75,
        uncertainty_handling=0.90,
        overall_score=0.88,
    )


def test_human_calibration_creates_record() -> None:
    service = HumanCalibrationService()

    record = service.calibrate(
        llm_result=make_llm_result(),
        human=make_human_label(),
    )

    assert isinstance(record, CalibrationRecord)
    assert record.llm_groundedness == pytest.approx(0.90)
    assert record.llm_completeness == pytest.approx(0.80)
    assert record.llm_uncertainty_handling == pytest.approx(0.85)
    assert record.llm_overall_score == pytest.approx(0.85)
    assert record.human.overall_score == pytest.approx(0.88)
    assert record.created_at.tzinfo == UTC


def test_human_calibration_fails_when_metric_is_missing() -> None:
    service = HumanCalibrationService()

    result = EvaluationResult(
        metrics=[
            EvaluationMetric(
                name="llm_groundedness",
                value=0.9,
                description="Groundedness.",
            ),
        ],
        overall_score=0.9,
    )

    with pytest.raises(
        ValueError,
        match="LLM evaluation missing metric",
    ):
        service.calibrate(
            llm_result=result,
            human=make_human_label(),
        )
