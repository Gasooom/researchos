"""Compare two ExperimentRun snapshots.

This is deliberately generic: it diffs whatever metric names two runs share,
without knowing what any of them mean. It refuses to compare runs over
different data (different dataset version or case set) because a delta
there wouldn't describe the same questions.

It is NOT a replacement for app.application.evaluation.comparison, which
encodes ResearchOS-specific knowledge of which M6 metrics changed meaning
under claim independence. That narrative belongs to that one transition and
stays there. This module is the general-purpose tool for comparing any two
experiment runs going forward.
"""

from pydantic import BaseModel, ConfigDict

from app.domain.experiments.models import ExperimentRun


class IncompatibleExperiments(Exception):
    """Raised when two runs cannot be meaningfully compared."""


class MetricComparison(BaseModel):
    """One metric's value across two runs, or an explicit note that it's missing."""

    model_config = ConfigDict(frozen=True)

    metric: str
    baseline: float | None
    candidate: float | None
    delta: float | None
    status: str  # "compared" | "missing_baseline" | "missing_candidate"


class ExperimentComparison(BaseModel):
    """The result of comparing two compatible experiment runs."""

    model_config = ConfigDict(frozen=True)

    baseline_run_id: str
    candidate_run_id: str
    metrics: tuple[MetricComparison, ...]


def _assert_compatible(baseline: ExperimentRun, candidate: ExperimentRun) -> None:
    """Refuse to compare runs whose dataset or case set differs."""
    if baseline.dataset_version != candidate.dataset_version:
        raise IncompatibleExperiments(
            f"dataset versions differ ({baseline.dataset_version} vs "
            f"{candidate.dataset_version}); metric deltas would not describe "
            "the same questions"
        )

    if set(baseline.case_ids) != set(candidate.case_ids):
        baseline_only = sorted(set(baseline.case_ids) - set(candidate.case_ids))
        candidate_only = sorted(set(candidate.case_ids) - set(baseline.case_ids))
        raise IncompatibleExperiments(
            f"case sets differ; baseline-only={baseline_only} "
            f"candidate-only={candidate_only}"
        )


def compare_experiment_runs(
    baseline: ExperimentRun,
    candidate: ExperimentRun,
) -> ExperimentComparison:
    """Compare two experiment runs metric by metric.

    Raises IncompatibleExperiments rather than silently comparing runs over
    different datasets or case sets. Metrics present on only one side are
    reported with an explicit "missing_*" status rather than a delta.
    """
    _assert_compatible(baseline, candidate)

    metric_names = sorted(set(baseline.metrics) | set(candidate.metrics))
    rows = []

    for name in metric_names:
        base_value = baseline.metrics.get(name)
        cand_value = candidate.metrics.get(name)

        if base_value is None:
            status = "missing_baseline"
        elif cand_value is None:
            status = "missing_candidate"
        else:
            status = "compared"

        delta = (
            None
            if base_value is None or cand_value is None
            else round(cand_value - base_value, 4)
        )

        rows.append(
            MetricComparison(
                metric=name,
                baseline=None if base_value is None else round(base_value, 4),
                candidate=None if cand_value is None else round(cand_value, 4),
                delta=delta,
                status=status,
            )
        )

    return ExperimentComparison(
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        metrics=tuple(rows),
    )
