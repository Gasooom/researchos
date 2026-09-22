"""Loading for the versioned ResearchOS benchmark dataset."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.evaluation.benchmark import BenchmarkCase

DATASET_PATH = Path(__file__).resolve().parents[3] / "benchmark" / "dataset.json"


class BenchmarkCaseSpec(BaseModel):
    """One dataset entry, including characteristics the judge and humans use."""

    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    difficulty: Literal["easy", "moderate", "hard"]
    domain: str = Field(min_length=1)
    uncertainty_expected: bool
    expected_focus: list[str] = Field(min_length=1)
    must_contain: list[str] = Field(min_length=1)
    must_avoid: list[str] = Field(min_length=1)

    def to_case(self) -> BenchmarkCase:
        """Project onto the evaluation model the deterministic pipeline consumes."""
        return BenchmarkCase(
            id=self.id,
            question=self.question,
            expected_focus=self.expected_focus,
        )


class BenchmarkDataset(BaseModel):
    """A versioned, reproducible set of benchmark cases."""

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    created: str = Field(min_length=1)
    case_count: int = Field(ge=1)
    cases: list[BenchmarkCaseSpec] = Field(min_length=1)

    def cases_by_id(self) -> dict[str, BenchmarkCaseSpec]:
        """Index specs by case id."""
        return {spec.id: spec for spec in self.cases}

    def to_cases(self) -> tuple[BenchmarkCase, ...]:
        """Project every spec onto the deterministic evaluation model."""
        return tuple(spec.to_case() for spec in self.cases)


@lru_cache
def load_benchmark_dataset(path: Path = DATASET_PATH) -> BenchmarkDataset:
    """Load and validate the versioned benchmark dataset."""
    dataset = BenchmarkDataset.model_validate(
        json.loads(path.read_text(encoding="utf-8")),
    )

    if dataset.case_count != len(dataset.cases):
        raise ValueError(
            f"benchmark dataset declares {dataset.case_count} cases "
            f"but contains {len(dataset.cases)}"
        )

    ids = [spec.id for spec in dataset.cases]

    if len(ids) != len(set(ids)):
        raise ValueError("benchmark dataset contains duplicate case ids")

    return dataset
