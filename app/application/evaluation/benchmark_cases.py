"""Reproducible benchmark cases for ResearchOS."""

from app.application.evaluation.benchmark_dataset import load_benchmark_dataset
from app.domain.evaluation.benchmark import BenchmarkCase


def get_benchmark_cases() -> tuple[BenchmarkCase, ...]:
    """Return the versioned ResearchOS benchmark dataset."""
    return load_benchmark_dataset().to_cases()
