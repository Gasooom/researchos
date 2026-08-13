import json

import pytest

from app.application.evaluation.llm_judge import LLMJudgeEvaluator
from app.domain.evaluation.models import EvaluationResult
from app.domain.research.models import (
    Claim,
    Evidence,
    ResearchResult,
    Source,
)


def make_result() -> ResearchResult:
    source = Source(
        title="AI Reliability",
        url="https://example.com/reliability",
        publisher="Example Research",
        retrieved_at="2026-08-13T10:00:00Z",
    )

    evidence = Evidence(
        source=source,
        excerpt="Evaluation improves AI agent reliability.",
        relevance=0.92,
    )

    claim = Claim(
        statement="Evaluation improves AI agent reliability.",
        evidence=[evidence],
    )

    return ResearchResult(
        question="How can AI agent reliability improve?",
        claims=[claim],
        sources=[source],
        execution=None,
    )


class StubJudge:
    """Deterministic LLM judge for unit tests."""

    def __init__(self) -> None:
        self.prompt: str | None = None

    def generate(self, prompt: str) -> list[dict[str, str]]:
        self.prompt = prompt

        return [
            {
                "judgment": json.dumps(
                    {
                        "groundedness": 0.95,
                        "completeness": 0.85,
                        "uncertainty_handling": 0.9,
                        "overall_score": 0.9,
                        "reasoning": (
                            "The claims are well supported by the provided evidence."
                        ),
                    }
                )
            }
        ]


def test_llm_judge_returns_evaluation_result() -> None:
    evaluator = LLMJudgeEvaluator(StubJudge())

    result = evaluator.evaluate(make_result())

    assert isinstance(result, EvaluationResult)
    assert result.overall_score == pytest.approx(0.9)
    assert len(result.metrics) == 4


def test_llm_judge_includes_research_context_in_prompt() -> None:
    provider = StubJudge()
    evaluator = LLMJudgeEvaluator(provider)

    evaluator.evaluate(make_result())

    assert provider.prompt is not None
    assert "How can AI agent reliability improve?" in provider.prompt
    assert "Evaluation improves AI agent reliability." in provider.prompt
    assert "Do not use outside knowledge." in provider.prompt


def test_llm_judge_rejects_missing_judgment() -> None:
    class InvalidProvider:
        def generate(self, prompt: str) -> list[dict[str, str]]:
            return [{"unexpected": "value"}]

    evaluator = LLMJudgeEvaluator(InvalidProvider())

    with pytest.raises(
        ValueError,
        match="must contain 'judgment'",
    ):
        evaluator.evaluate(make_result())


def test_llm_judge_rejects_invalid_json() -> None:
    class InvalidProvider:
        def generate(self, prompt: str) -> list[dict[str, str]]:
            return [{"judgment": "not-json"}]

    evaluator = LLMJudgeEvaluator(InvalidProvider())

    with pytest.raises(
        ValueError,
        match="returned invalid JSON",
    ):
        evaluator.evaluate(make_result())


def test_llm_judge_requires_exactly_one_provider_result() -> None:
    class InvalidProvider:
        def generate(self, prompt: str) -> list[dict[str, str]]:
            return [
                {"judgment": "{}"},
                {"judgment": "{}"},
            ]

    evaluator = LLMJudgeEvaluator(InvalidProvider())

    with pytest.raises(
        ValueError,
        match="exactly one result",
    ):
        evaluator.evaluate(make_result())
