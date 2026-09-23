import pytest

from app.application.evaluation.comparison import (
    IncompatibleBenchmarks,
    build_comparison,
    metric_mean,
)


def make_run(
    metrics_by_case: dict[str, dict[str, float]],
    dataset_version: str = "1.0.0",
    git_commit: str = "abc1234",
    statuses: dict[str, str] | None = None,
) -> dict:
    statuses = statuses or {}

    return {
        "run": {
            "git_commit": git_commit,
            "llm_model": "gpt-5-mini",
            "dataset_version": dataset_version,
            "started_at": "2026-09-22T00:00:00+00:00",
            "cases_ok": sum(
                1 for case in metrics_by_case if statuses.get(case, "ok") == "ok"
            ),
            "cases_error": sum(
                1 for case in metrics_by_case if statuses.get(case, "ok") != "ok"
            ),
        },
        "results": [
            {
                "id": case,
                "status": statuses.get(case, "ok"),
                "metrics": metrics,
            }
            for case, metrics in metrics_by_case.items()
        ],
    }


def test_metric_mean_averages_only_successful_cases() -> None:
    run = make_run(
        {"a": {"focus_coverage": 1.0}, "b": {"focus_coverage": 0.0}},
        statuses={"b": "error"},
    )

    assert metric_mean(run, "focus_coverage") == 1.0


def test_metric_mean_returns_none_for_absent_metric() -> None:
    assert metric_mean(make_run({"a": {"focus_coverage": 1.0}}), "nope") is None


def test_differing_dataset_versions_are_refused() -> None:
    baseline = make_run({"a": {"task_success_rate": 1.0}}, dataset_version="1.0.0")
    candidate = make_run({"a": {"task_success_rate": 1.0}}, dataset_version="2.0.0")

    with pytest.raises(IncompatibleBenchmarks, match="dataset versions differ"):
        build_comparison(baseline, candidate)


def test_differing_case_sets_are_refused() -> None:
    baseline = make_run({"a": {"task_success_rate": 1.0}})
    candidate = make_run({"b": {"task_success_rate": 1.0}})

    with pytest.raises(IncompatibleBenchmarks, match="case sets differ"):
        build_comparison(baseline, candidate)


def test_comparable_metrics_report_a_delta() -> None:
    baseline = make_run({"a": {"average_relevance": 0.70}})
    candidate = make_run({"a": {"average_relevance": 0.80}})

    comparison = build_comparison(baseline, candidate)

    row = next(
        r for r in comparison["comparable"] if r["metric"] == "average_relevance"
    )

    assert row["baseline"] == 0.70
    assert row["candidate"] == 0.80
    assert row["delta"] == pytest.approx(0.10)


def test_renamed_metric_compares_across_its_old_and_new_key() -> None:
    """A legacy run records claim_support_rate; a current run records the rename."""
    baseline = make_run({"a": {"claim_support_rate": 0.40}})
    candidate = make_run({"a": {"high_relevance_claim_rate": 0.55}})

    comparison = build_comparison(baseline, candidate)

    row = next(
        r
        for r in comparison["renamed_population_changed"]
        if r["metric"].startswith("claim_support_rate")
    )

    assert row["baseline"] == 0.40
    assert row["candidate"] == 0.55
    assert row["delta"] == pytest.approx(0.15)


def test_renamed_metrics_are_not_presented_as_comparable() -> None:
    """The formula is unchanged but M6 changed the claim population it runs over.

    A claim used to carry one evidence item, so "any evidence >= 0.8" tested that
    item. A synthesized claim carries its whole task's evidence, so the same
    expression now tests the maximum across the set and rises structurally. The
    delta must not sit in the comparable group.
    """
    baseline = make_run({"a": {"claim_support_rate": 0.35}})
    candidate = make_run({"a": {"high_relevance_claim_rate": 1.0}})

    comparison = build_comparison(baseline, candidate)

    comparable = {row["metric"] for row in comparison["comparable"]}

    assert not any("claim_support_rate" in metric for metric in comparable)
    assert not any("high_relevance_claim_rate" in metric for metric in comparable)
    assert "move by construction" in comparison["interpretation"]


def test_judge_metrics_are_grouped_as_claim_text_changed_not_improvements() -> None:
    """The judge reads claim.statement, which M6 redefined."""
    baseline = make_run({"a": {"llm_judge_overall": 0.50}})
    candidate = make_run({"a": {"llm_judge_overall": 0.90}})

    comparison = build_comparison(baseline, candidate)

    changed = {row["metric"] for row in comparison["claim_text_changed"]}
    comparable = {row["metric"] for row in comparison["comparable"]}

    assert "llm_judge_overall" in changed
    assert "llm_judge_overall" not in comparable
    assert "improvement or regression" in comparison["interpretation"]
    assert "different text" in comparison["interpretation"]


def test_claim_evidence_metrics_are_grouped_separately_from_claim_text_metrics() -> (
    None
):
    """claim_source_diversity iterates claim.evidence, not claim.statement.

    Its mechanism is the same population change as the renamed group (a claim's
    evidence list now holds a whole task's evidence instead of one item), not
    the text-content change judge metrics undergo. Conflating the two would
    misattribute why the number moved.
    """
    baseline = make_run({"a": {"claim_source_diversity": 0.97}})
    candidate = make_run({"a": {"claim_source_diversity": 0.59}})

    comparison = build_comparison(baseline, candidate)

    population = {row["metric"] for row in comparison["claim_population_changed"]}
    text = {row["metric"] for row in comparison["claim_text_changed"]}

    assert "claim_source_diversity" in population
    assert "claim_source_diversity" not in text


def test_metrics_absent_from_the_baseline_are_reported_as_new() -> None:
    baseline = make_run({"a": {"task_success_rate": 1.0}})
    candidate = make_run(
        {"a": {"task_success_rate": 1.0, "claim_evidence_overlap_rate": 0.62}},
    )

    comparison = build_comparison(baseline, candidate)

    new_rows = {row["metric"]: row for row in comparison["new_in_candidate"]}

    assert "claim_evidence_overlap_rate" in new_rows
    assert new_rows["claim_evidence_overlap_rate"]["candidate"] == 0.62
    assert new_rows["claim_evidence_overlap_rate"]["delta"] is None


def test_missing_metrics_produce_no_delta_rather_than_a_guess() -> None:
    baseline = make_run({"a": {"task_success_rate": 1.0}})
    candidate = make_run({"a": {"task_success_rate": 1.0}})

    comparison = build_comparison(baseline, candidate)

    row = next(
        r for r in comparison["claim_text_changed"] if r["metric"] == "focus_coverage"
    )

    assert row["baseline"] is None
    assert row["candidate"] is None
    assert row["delta"] is None


def test_comparison_records_reproducibility_metadata_for_both_runs() -> None:
    baseline = make_run({"a": {"task_success_rate": 1.0}}, git_commit="1111111")
    candidate = make_run({"a": {"task_success_rate": 1.0}}, git_commit="2222222")

    comparison = build_comparison(baseline, candidate)

    assert comparison["baseline"]["git_commit"] == "1111111"
    assert comparison["candidate"]["git_commit"] == "2222222"
    assert comparison["baseline"]["dataset_version"] == "1.0.0"
    assert comparison["candidate"]["llm_model"] == "gpt-5-mini"
