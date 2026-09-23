from datetime import UTC, datetime

import pytest

from app.application.experiments.comparison import (
    IncompatibleExperiments,
    compare_experiment_runs,
)
from app.domain.experiments.models import ExperimentRun


def make_run(**overrides) -> ExperimentRun:
    defaults = dict(
        experiment_name="researchos-benchmark",
        git_commit="abc123",
        dataset_name="researchos-benchmark",
        dataset_version="1.0.0",
        provider="openai",
        model="gpt-5-mini",
        configuration={"llm_mode": "openai", "llm_model": "gpt-5-mini"},
        started_at=datetime(2026, 9, 22, tzinfo=UTC),
        case_ids=("case-a", "case-b"),
        cases_ok=2,
        cases_error=0,
        metrics={"average_relevance": 0.8, "task_success_rate": 1.0},
        source_path="benchmark/results/example.json",
    )
    defaults.update(overrides)
    return ExperimentRun(**defaults)


def test_reproducibility_metadata_is_identical_for_the_same_run_loaded_twice() -> None:
    a = make_run()
    b = make_run()

    assert a.run_id == b.run_id
    assert a == b


def test_different_dataset_versions_are_distinguishable() -> None:
    a = make_run()
    b = make_run(dataset_version="1.1.0")

    assert a.run_id != b.run_id


def test_different_git_commits_are_distinguishable() -> None:
    a = make_run()
    b = make_run(git_commit="def456")

    assert a.run_id != b.run_id


def test_different_configuration_is_distinguishable() -> None:
    a = make_run()
    b = make_run(configuration={"llm_mode": "openai", "llm_model": "gpt-5"})

    assert a.run_id != b.run_id


def test_metric_deltas_are_calculated_correctly() -> None:
    baseline = make_run(metrics={"average_relevance": 0.70, "task_success_rate": 0.9})
    candidate = make_run(metrics={"average_relevance": 0.85, "task_success_rate": 0.9})

    comparison = compare_experiment_runs(baseline, candidate)
    by_name = {row.metric: row for row in comparison.metrics}

    assert by_name["average_relevance"].delta == pytest.approx(0.15)
    assert by_name["average_relevance"].status == "compared"
    assert by_name["task_success_rate"].delta == pytest.approx(0.0)


def test_missing_metrics_are_reported_explicitly_not_silently_dropped() -> None:
    baseline = make_run(metrics={"average_relevance": 0.7, "legacy_metric": 0.5})
    candidate = make_run(metrics={"average_relevance": 0.8, "new_metric": 0.6})

    comparison = compare_experiment_runs(baseline, candidate)
    by_name = {row.metric: row for row in comparison.metrics}

    assert by_name["legacy_metric"].status == "missing_candidate"
    assert by_name["legacy_metric"].delta is None
    assert by_name["legacy_metric"].baseline == 0.5

    assert by_name["new_metric"].status == "missing_baseline"
    assert by_name["new_metric"].delta is None
    assert by_name["new_metric"].candidate == 0.6


def test_comparing_different_dataset_versions_raises_instead_of_comparing() -> None:
    baseline = make_run(dataset_version="1.0.0")
    candidate = make_run(dataset_version="2.0.0")

    with pytest.raises(IncompatibleExperiments, match="dataset versions differ"):
        compare_experiment_runs(baseline, candidate)


def test_comparing_different_case_sets_raises_instead_of_comparing() -> None:
    baseline = make_run(case_ids=("case-a", "case-b"))
    candidate = make_run(case_ids=("case-a", "case-c"))

    with pytest.raises(IncompatibleExperiments, match="case sets differ"):
        compare_experiment_runs(baseline, candidate)


def test_historical_run_objects_cannot_be_mutated_by_a_comparison() -> None:
    baseline = make_run()
    candidate = make_run(metrics={"average_relevance": 0.9, "task_success_rate": 1.0})

    original_metrics = dict(baseline.metrics)
    compare_experiment_runs(baseline, candidate)

    assert baseline.metrics == original_metrics
