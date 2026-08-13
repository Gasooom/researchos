"""Reproducible benchmark cases for ResearchOS."""

from app.domain.evaluation.benchmark import BenchmarkCase

BENCHMARK_CASES: tuple[BenchmarkCase, ...] = (
    BenchmarkCase(
        id="multi-agent-reliability",
        question=("How do multi-agent AI systems improve research reliability?"),
        expected_focus=[
            "specialized agent roles",
            "cross-checking and verification",
            "failure modes and limitations",
            "evaluation and observability",
        ],
    ),
    BenchmarkCase(
        id="research-groundedness",
        question=("How can evidence-grounded AI systems reduce unsupported claims?"),
        expected_focus=[
            "evidence retrieval",
            "claim support",
            "source verification",
            "grounded synthesis",
        ],
    ),
    BenchmarkCase(
        id="multi-agent-tradeoffs",
        question=(
            "What are the main tradeoffs of using multi-agent AI systems "
            "for complex research?"
        ),
        expected_focus=[
            "reliability",
            "latency",
            "cost",
            "coordination complexity",
            "failure modes",
        ],
    ),
)


def get_benchmark_cases() -> tuple[BenchmarkCase, ...]:
    """Return the reproducible ResearchOS benchmark dataset."""
    return BENCHMARK_CASES
