# Reproducible experiments

An `ExperimentRun` answers one question: what produced these metrics? It's a
read-only snapshot of a single completed benchmark run, built from a
committed `benchmark/results/*.json` file without ever writing to it.

```
Experiment (a name, e.g. "researchos-benchmark")
  -> dataset version    (from the result file's `run.dataset_version`)
  -> system/model        (`run.llm_mode` / `run.llm_model`)
  -> configuration       (provider + model, extensible with anything else
                           that varied between runs)
  -> a run               (one execution: started_at, git commit, case ids)
  -> metrics              (each metric name averaged over successful cases)
  -> comparison           (two runs, diffed metric by metric)
```

This is deliberately small: one frozen domain model
(`app/domain/experiments/models.py`), a loader
(`app/application/experiments/loader.py`), and a comparison service
(`app/application/experiments/comparison.py`). It does not track experiments
in a database, does not schedule runs, and does not have a UI - it exists to
make "did this get better" a question with a checkable answer, not a
platform.

## Loading a run

```python
from pathlib import Path
from app.application.experiments.loader import load_experiment_run

run = load_experiment_run(
    Path("benchmark/results/2026-09-22-d629756.json"),
    experiment_name="researchos-benchmark",
)

run.dataset_version  # "1.0.0"
run.git_commit  # the commit the run was executed at
run.provider  # "openai"
run.model  # "gpt-5-mini"
run.metrics["average_relevance"]  # mean across the 30 successful cases
run.run_id  # stable identity: same inputs -> same id, always
```

`run` is frozen (`model_config = ConfigDict(frozen=True)`): nothing in the
process can mutate a loaded snapshot, matching the "never mutate old
benchmark artifacts" rule the underlying JSON files are already held to.

## Comparing two runs

```python
from app.application.experiments.comparison import compare_experiment_runs

comparison = compare_experiment_runs(baseline_run, candidate_run)

for row in comparison.metrics:
    print(row.metric, row.baseline, "->", row.candidate, row.delta, row.status)
```

`compare_experiment_runs` raises `IncompatibleExperiments` instead of
producing a number when the two runs don't describe the same questions:
different `dataset_version`, or a different set of case ids. A metric present
on only one side is reported with `status="missing_baseline"` or
`"missing_candidate"` and `delta=None` - never silently treated as zero.

CLI: `python scripts/compare_experiments.py <baseline.json> <candidate.json>`.

## What this is not

This module has **no ResearchOS-specific knowledge** of what changed between
any two particular runs. Comparing `benchmark/results/2026-09-22.json`
against `2026-09-22-d629756.json` (the M6 claim-independence change) with
this tool shows `claim_support_rate` as `missing_candidate` and
`high_relevance_claim_rate` as `missing_baseline`, because M6 renamed the
metric - a plain string comparison can't know that's a rename rather than a
disappearance.

That narrative - which metrics are the same computation, which changed
meaning, and why - is intentionally kept separate, in
`app/application/evaluation/comparison.py`, scoped to that one transition.
Use this module for general "compare two runs" questions; use that one to
understand the specific M6 before/after story.

## Tests

- `tests/unit/experiments/test_experiment_run_loader.py` - reproducibility
  metadata capture, per-metric averaging over only the cases that report a
  metric, read-only loading, immutability.
- `tests/unit/experiments/test_experiment_comparison.py` - same-run identity
  is stable, different dataset/commit/configuration are distinguishable,
  delta calculation, explicit missing-metric handling, incompatible runs
  raise rather than compare.
- `tests/integration/experiments/test_real_benchmark_artifacts.py` - the
  same behaviour against the real, committed `2026-09-22.json` and
  `2026-09-22-d629756.json` artifacts.
