"""Prove the experiment abstraction works against real, committed benchmark
artifacts - not synthetic fixtures - without modifying them.
"""

from pathlib import Path

from app.application.experiments.comparison import compare_experiment_runs
from app.application.experiments.loader import load_experiment_run

RESULTS_DIR = Path(__file__).resolve().parents[3] / "benchmark" / "results"
PRE_M6 = RESULTS_DIR / "2026-09-22.json"
POST_M6 = RESULTS_DIR / "2026-09-22-d629756.json"


def test_loading_a_real_historical_result_does_not_modify_it() -> None:
    before = PRE_M6.read_bytes()

    run = load_experiment_run(PRE_M6, experiment_name="researchos-benchmark")

    assert PRE_M6.read_bytes() == before
    assert run.dataset_version == "1.0.0"
    assert run.cases_ok == 30
    assert len(run.case_ids) == 30


def test_two_real_runs_on_the_same_dataset_version_compare_cleanly() -> None:
    baseline = load_experiment_run(PRE_M6, experiment_name="researchos-benchmark")
    candidate = load_experiment_run(POST_M6, experiment_name="researchos-benchmark")

    comparison = compare_experiment_runs(baseline, candidate)
    by_name = {row.metric: row for row in comparison.metrics}

    # average_relevance is computed the same way before and after M6, so it's
    # directly comparable - unlike claim_support_rate, which M6 renamed and
    # changed the meaning of (see app.application.evaluation.comparison for
    # that ResearchOS-specific narrative).
    assert by_name["average_relevance"].status == "compared"

    # The M6 rename means the old and new names are literally different
    # strings to this generic comparator, so each shows as missing on one
    # side - correctly, since this module has no ResearchOS-specific
    # knowledge of the rename.
    assert by_name["claim_support_rate"].status == "missing_candidate"
    assert by_name["high_relevance_claim_rate"].status == "missing_baseline"
