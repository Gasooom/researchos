from app.domain.evaluation.models import EvaluationMetric, EvaluationResult


def test_evaluation_metric_accepts_valid_data() -> None:
    metric = EvaluationMetric(
        name="claim_support_rate",
        value=0.92,
        description="Fraction of claims supported by evidence.",
    )

    assert metric.name == "claim_support_rate"
    assert metric.value == 0.92


def test_evaluation_result_accepts_valid_data() -> None:
    result = EvaluationResult(
        metrics=[
            EvaluationMetric(
                name="claim_support_rate",
                value=0.92,
                description="Fraction of claims supported by evidence.",
            )
        ],
        overall_score=0.92,
    )

    assert result.overall_score == 0.92
    assert len(result.metrics) == 1
