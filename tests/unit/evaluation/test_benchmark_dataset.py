import json

import pytest
from pydantic import ValidationError

from app.application.evaluation.benchmark_dataset import (
    BenchmarkDataset,
    load_benchmark_dataset,
)


def _dataset_payload(**overrides) -> dict:
    payload = {
        "name": "test-benchmark",
        "version": "1.0.0",
        "created": "2026-09-22",
        "case_count": 1,
        "cases": [
            {
                "id": "example-case",
                "question": "What is an example question?",
                "difficulty": "easy",
                "domain": "testing",
                "uncertainty_expected": False,
                "expected_focus": ["example focus"],
                "must_contain": ["a required characteristic"],
                "must_avoid": ["a disqualifying characteristic"],
            }
        ],
    }

    payload.update(overrides)

    return payload


def test_dataset_validates_a_well_formed_payload() -> None:
    dataset = BenchmarkDataset.model_validate(_dataset_payload())

    assert dataset.case_count == 1
    assert dataset.cases[0].id == "example-case"


def test_spec_projects_onto_benchmark_case() -> None:
    dataset = BenchmarkDataset.model_validate(_dataset_payload())

    case = dataset.cases[0].to_case()

    assert case.id == "example-case"
    assert case.question == "What is an example question?"
    assert case.expected_focus == ["example focus"]


def test_dataset_rejects_unknown_difficulty() -> None:
    payload = _dataset_payload()
    payload["cases"][0]["difficulty"] = "trivial"

    with pytest.raises(ValidationError):
        BenchmarkDataset.model_validate(payload)


def test_dataset_rejects_empty_characteristics() -> None:
    payload = _dataset_payload()
    payload["cases"][0]["must_contain"] = []

    with pytest.raises(ValidationError):
        BenchmarkDataset.model_validate(payload)


def test_loader_rejects_declared_count_mismatch(tmp_path) -> None:
    path = tmp_path / "dataset.json"
    path.write_text(
        json.dumps(_dataset_payload(case_count=7)),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="declares 7 cases"):
        load_benchmark_dataset(path)


def test_loader_rejects_duplicate_ids(tmp_path) -> None:
    payload = _dataset_payload(case_count=2)
    payload["cases"].append(dict(payload["cases"][0]))

    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate case ids"):
        load_benchmark_dataset(path)


def test_shipped_dataset_loads_and_matches_its_declared_count() -> None:
    dataset = load_benchmark_dataset()

    assert dataset.case_count == len(dataset.cases)
    assert len(dataset.to_cases()) == dataset.case_count


def test_shipped_dataset_ids_are_unique_and_indexable() -> None:
    dataset = load_benchmark_dataset()

    index = dataset.cases_by_id()

    assert len(index) == len(dataset.cases)
