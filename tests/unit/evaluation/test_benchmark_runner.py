from datetime import UTC, datetime

from app.application.evaluation.benchmark_runner import (
    BaselineResearchRunner,
)
from app.domain.evaluation.benchmark import BenchmarkCase
from app.domain.evaluation.models import EvaluationMetric, EvaluationResult
from app.domain.research.models import Evidence, Source


class StubResearchAgent:
    """Deterministic baseline agent for benchmark tests."""

    def research(self, task):
        source = Source(
            title="Benchmark Source",
            url="https://example.com/benchmark",
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

        return [
            Evidence(
                source=source,
                excerpt="Benchmark evidence.",
                relevance=0.9,
            )
        ]


class StubSystemReportBuilder:
    """Deterministic system report builder."""

    def build(self, result):
        return EvaluationResult(
            metrics=[
                EvaluationMetric(
                    name="overall_research_quality",
                    value=0.8,
                    description="Research quality.",
                ),
                EvaluationMetric(
                    name="task_success_rate",
                    value=1.0,
                    description="Task success rate.",
                ),
                EvaluationMetric(
                    name="failure_rate",
                    value=0.0,
                    description="Failure rate.",
                ),
                EvaluationMetric(
                    name="semantic_quality",
                    value=0.8,
                    description="Semantic quality.",
                ),
            ],
            overall_score=0.8,
        )


class StubBenchmarkReportBuilder:
    """Deterministic benchmark report builder for runner tests."""

    def __init__(self) -> None:
        self.calls = []

    def build(self, case, result):
        self.calls.append(
            {
                "case": case,
                "result": result,
            }
        )

        return EvaluationResult(
            metrics=[
                EvaluationMetric(
                    name="benchmark_score",
                    value=0.8,
                    description="Deterministic benchmark score.",
                )
            ],
            overall_score=0.8,
        )


def make_case() -> BenchmarkCase:
    return BenchmarkCase(
        id="test-case",
        question="How do AI systems improve reliability?",
        expected_focus=["reliability"],
    )


def test_baseline_runner_returns_result_and_report() -> None:
    report_builder = StubBenchmarkReportBuilder()

    runner = BaselineResearchRunner(
        research_agent=StubResearchAgent(),
        report_builder=report_builder,
    )

    result, report = runner.run(make_case())

    assert result.question == "How do AI systems improve reliability?"
    assert len(result.sources) == 1
    assert len(result.claims) == 1
    assert result.execution is not None
    assert result.execution.status.value == "success"
    assert report.overall_score == 0.8
    assert len(report_builder.calls) == 1


def test_baseline_runner_uses_one_research_task() -> None:
    class RecordingAgent:
        def __init__(self) -> None:
            self.task = None

        def research(self, task):
            self.task = task

            source = Source(
                title="Benchmark Source",
                url="https://example.com/benchmark",
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

            return [
                Evidence(
                    source=source,
                    excerpt="Benchmark evidence.",
                    relevance=0.9,
                )
            ]

    agent = RecordingAgent()

    runner = BaselineResearchRunner(
        research_agent=agent,
        report_builder=StubBenchmarkReportBuilder(),
    )

    runner.run(make_case())

    assert agent.task is not None
    assert agent.task.task_type == "baseline"
    assert agent.task.objective == "How do AI systems improve reliability?"
