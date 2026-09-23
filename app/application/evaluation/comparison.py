"""Comparison between two recorded benchmark runs.

Metrics are grouped by whether a delta is interpretable at all. A number that
moved because the pipeline now feeds the evaluator different text is not an
improvement, and this module refuses to present it as one.
"""

import statistics

# Same computation, same inputs before and after claim independence (M6).
COMPARABLE = (
    "task_success_rate",
    "failure_rate",
    "partial_run_rate",
    "average_relevance",
    "high_relevance_rate",
)

# Renamed in M6 Stage 1. The computation is identical (proven by a differential
# test), so the old and new keys line up as one row. The delta is still not an
# improvement: M6 Stage 3 changed the claim population these run over. A claim
# used to carry exactly one evidence item, so "any evidence >= 0.8" tested that
# item; a synthesized claim carries its whole task's evidence, so the same
# expression now tests the maximum across the set and trends higher for
# structural reasons.
RENAMED = {
    "claim_support_rate": "high_relevance_claim_rate",
    "unsupported_claim_rate": "low_relevance_claim_rate",
}

# These iterate claim.evidence, not claim.statement. M6 Stage 3 changed what
# each claim's evidence list contains: a claim used to carry exactly one
# evidence item (its own excerpt); a synthesized claim carries its whole task's
# evidence set. Metrics built from claim.evidence structure move for that
# reason alone, independent of what the claim says.
CLAIM_POPULATION_CHANGED = (
    "claim_source_diversity",
    "evidence_breadth",
    "evidence_coverage",
)

# These read claim.statement, which M6 redefined from "the evidence excerpt" to
# "a synthesized finding". The evaluator scores different text, so a delta
# records that semantic change, not better or worse research.
CLAIM_TEXT_CHANGED = (
    "llm_groundedness",
    "llm_completeness",
    "llm_uncertainty_handling",
    "llm_judge_overall",
    "llm_judge_adjusted_quality",
    "focus_coverage",
)

# Composite scores built from a mix of the metrics above, so they inherit both
# effects and cannot be attributed to either one alone.
COMPOSITE_CHANGED = (
    "semantic_quality",
    "overall_research_quality",
    "overall_system_quality",
)

INTERPRETATION = (
    "Only deltas under 'comparable' describe the same computation over the same "
    "inputs. Everything else moved for structural reasons and must not be read "
    "as improvement or regression. 'renamed_population_changed' and "
    "'claim_population_changed' apply an unchanged formula to a different claim "
    "population: a claim used to carry one evidence item and now carries its "
    "whole task's evidence, so evidence-derived metrics move by construction. "
    "'claim_text_changed' metrics read claim.statement, which M6 redefined from "
    "the evidence excerpt to a synthesized finding, so the evaluator is scoring "
    "different text. 'composite_changed' metrics combine both effects and "
    "cannot be attributed to either alone."
)


class IncompatibleBenchmarks(Exception):
    """Raised when two runs cannot be meaningfully compared."""


def metric_mean(payload: dict, name: str) -> float | None:
    """Average one metric across successful cases, or None when absent."""
    values = [
        record["metrics"][name]
        for record in payload["results"]
        if record["status"] == "ok" and name in record["metrics"]
    ]

    return statistics.fmean(values) if values else None


def _metric_names(payload: dict) -> set[str]:
    """Collect every metric name recorded by successful cases."""
    return {
        name
        for record in payload["results"]
        if record["status"] == "ok"
        for name in record["metrics"]
    }


def _row(metric: str, base: float | None, cand: float | None) -> dict:
    """Build one comparison row, leaving deltas absent when either side is."""
    return {
        "metric": metric,
        "baseline": None if base is None else round(base, 4),
        "candidate": None if cand is None else round(cand, 4),
        "delta": (None if base is None or cand is None else round(cand - base, 4)),
    }


def assert_compatible(baseline: dict, candidate: dict) -> None:
    """Refuse to compare runs whose dataset or case set differs."""
    base_version = baseline["run"]["dataset_version"]
    cand_version = candidate["run"]["dataset_version"]

    if base_version != cand_version:
        raise IncompatibleBenchmarks(
            f"dataset versions differ ({base_version} vs {cand_version}); "
            "metric deltas would not describe the same questions"
        )

    base_ids = {record["id"] for record in baseline["results"]}
    cand_ids = {record["id"] for record in candidate["results"]}

    if base_ids != cand_ids:
        raise IncompatibleBenchmarks(
            "case sets differ; "
            f"baseline-only={sorted(base_ids - cand_ids)} "
            f"candidate-only={sorted(cand_ids - base_ids)}"
        )


def _run_summary(payload: dict) -> dict:
    """Capture the reproducibility metadata recorded with a run."""
    run = payload["run"]

    return {
        "git_commit": run["git_commit"],
        "llm_model": run["llm_model"],
        "dataset_version": run["dataset_version"],
        "started_at": run["started_at"],
        "cases_ok": run["cases_ok"],
        "cases_error": run["cases_error"],
    }


def build_comparison(baseline: dict, candidate: dict) -> dict:
    """Compare two runs, grouped by whether deltas are interpretable."""
    assert_compatible(baseline, candidate)

    comparable = [
        _row(name, metric_mean(baseline, name), metric_mean(candidate, name))
        for name in COMPARABLE
    ]

    renamed = []

    for old_name, new_name in RENAMED.items():
        base = metric_mean(baseline, old_name)

        if base is None:
            base = metric_mean(baseline, new_name)

        cand = metric_mean(candidate, new_name)

        if cand is None:
            cand = metric_mean(candidate, old_name)

        renamed.append(_row(f"{old_name} -> {new_name}", base, cand))

    claim_population = [
        _row(name, metric_mean(baseline, name), metric_mean(candidate, name))
        for name in CLAIM_POPULATION_CHANGED
    ]

    claim_text = [
        _row(name, metric_mean(baseline, name), metric_mean(candidate, name))
        for name in CLAIM_TEXT_CHANGED
    ]

    composite = [
        _row(name, metric_mean(baseline, name), metric_mean(candidate, name))
        for name in COMPOSITE_CHANGED
    ]

    introduced = [
        _row(name, None, metric_mean(candidate, name))
        for name in sorted(_metric_names(candidate) - _metric_names(baseline))
    ]

    return {
        "baseline": _run_summary(baseline),
        "candidate": _run_summary(candidate),
        "comparable": comparable,
        "renamed_population_changed": renamed,
        "claim_population_changed": claim_population,
        "claim_text_changed": claim_text,
        "composite_changed": composite,
        "new_in_candidate": introduced,
        "interpretation": INTERPRETATION,
    }
