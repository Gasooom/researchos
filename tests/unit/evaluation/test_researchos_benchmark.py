from datetime import UTC, datetime

import pytest

from app.application.evaluation.researchos_benchmark import (
    ResearchOSBenchmarkRunner,
)
from app.domain.evaluation.benchmark import (
    BenchmarkCase,
    BenchmarkExecutionResult,
)
from app.domain.evaluation.models import EvaluationMetric, EvaluationResult
from app.domain.research.models import (
    Claim,
    Evidence,
    ResearchResult,
    Source,
)
from app.domain.runs.models import ResearchRunOutcome, ResearchRunStatus


class StubResearchService:
    """Deterministic ResearchOS service for benchmark tests."""

    def __init__(self) -> None:
        self.request = None

    def execute_with_evaluation_artifacts(
        self,
        request,
    ):
        """Execute a deterministic benchmark request."""
        self.request = request

        source = Source(
            title="ResearchOS Source",
            url="https://example.com/researchos",
            publisher="Example Research",
            retrieved_at=datetime(
                2026,
                8,
                13,
                16,
                0,
                tzinfo=UTC,
            ),
        )

        evidence = Evidence(
            source=source,
            excerpt="ResearchOS evidence.",
            relevance=0.95,
        )

        claim = Claim(
            statement="ResearchOS claim.",
            evidence=[evidence],
        )

        outcome = ResearchRunOutcome(
            status=ResearchRunStatus.SUCCESS,
            completed_tasks=3,
            failed_tasks=0,
            failures=[],
            evidence=[evidence],
        )

        result = ResearchResult(
            question=request.question,
            claims=[claim],
            sources=[source],
            execution=outcome,
        )

        return (
            result,
            outcome,
            [],
        )

    def execute(
        self,
        request,
    ):
        """Execute a request through the compatibility path."""
        result, _, _ = self.execute_with_evaluation_artifacts(request)

        return result


class StubBenchmarkReportBuilder:
    """Deterministic benchmark report builder."""

    def build(
        self,
        case,
        result,
        multi_agent_results=None,
    ):
        return EvaluationResult(
            metrics=[
                EvaluationMetric(
                    name="benchmark_score",
                    value=0.9,
                    description="Deterministic benchmark score.",
                )
            ],
            overall_score=0.9,
        )


def make_case() -> BenchmarkCase:
    return BenchmarkCase(
        id="researchos-test-case",
        question="How do AI systems improve reliability?",
        expected_focus=["reliability"],
    )


def test_researchos_runner_returns_result_and_report() -> None:
    service = StubResearchService()

    runner = ResearchOSBenchmarkRunner(
        service=service,
        report_builder=StubBenchmarkReportBuilder(),
    )

    execution, report = runner.run(make_case())

    assert isinstance(
        execution,
        BenchmarkExecutionResult,
    )

    assert execution.result.question == "How do AI systems improve reliability?"

    assert execution.result.execution is not None
    assert execution.result.execution.status == ResearchRunStatus.SUCCESS
    assert execution.result.execution.completed_tasks == 3
    assert len(execution.result.claims) == 1
    assert len(execution.result.sources) == 1
    assert execution.multi_agent_results == []
    assert report.overall_score == 0.9


def test_researchos_runner_passes_benchmark_question_to_service() -> None:
    service = StubResearchService()

    runner = ResearchOSBenchmarkRunner(
        service=service,
        report_builder=StubBenchmarkReportBuilder(),
    )

    runner.run(make_case())

    assert service.request is not None
    assert service.request.question == "How do AI systems improve reliability?"
    assert service.request.max_sources == 3


def test_researchos_runner_requires_execution_outcome() -> None:
    class NoExecutionService:
        def execute_with_evaluation_artifacts(
            self,
            request,
        ):
            source = Source(
                title="ResearchOS Source",
                url="https://example.com/researchos",
                publisher="Example Research",
                retrieved_at=datetime(
                    2026,
                    8,
                    13,
                    16,
                    0,
                    tzinfo=UTC,
                ),
            )

            evidence = Evidence(
                source=source,
                excerpt="Evidence.",
                relevance=0.9,
            )

            result = ResearchResult(
                question=request.question,
                claims=[
                    Claim(
                        statement="Claim.",
                        evidence=[evidence],
                    )
                ],
                sources=[source],
                execution=None,
            )

            return result, None, []

    runner = ResearchOSBenchmarkRunner(
        service=NoExecutionService(),
        report_builder=StubBenchmarkReportBuilder(),
    )

    with pytest.raises(
        ValueError,
        match="no execution outcome",
    ):
        runner.run(make_case())
