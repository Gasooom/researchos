from app.domain.evaluation.models import EvaluationMetric, EvaluationResult


def test_evaluation_metric_accepts_valid_data() -> None:
    metric = EvaluationMetric(
        name="high_relevance_claim_rate",
        value=0.92,
        description="Fraction of claims whose best evidence cleared 0.8 relevance.",
    )

    assert metric.name == "high_relevance_claim_rate"
    assert metric.value == 0.92


def test_evaluation_result_accepts_valid_data() -> None:
    result = EvaluationResult(
        metrics=[
            EvaluationMetric(
                name="high_relevance_claim_rate",
                value=0.92,
                description=(
                    "Fraction of claims whose best evidence cleared 0.8 relevance."
                ),
            )
        ],
        overall_score=0.92,
    )

    assert result.overall_score == 0.92
    assert len(result.metrics) == 1
