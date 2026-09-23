"""Load a benchmark result file as an ExperimentRun snapshot.

Read-only: this module never writes to a result file. Committed results are
historical artifacts (see scripts/run_benchmark.py's overwrite guard) and
loading one must not be able to mutate it.
"""

import json
import statistics
from pathlib import Path

from app.domain.experiments.models import ExperimentRun


def _metric_means(results: list[dict]) -> dict[str, float]:
    """Average each metric across successful cases only.

    A metric that only some cases report (e.g. added mid-dataset, or
    conditional on case characteristics) is averaged over the cases that
    reported it, not treated as zero for the rest.
    """
    values_by_metric: dict[str, list[float]] = {}

    for record in results:
        if record["status"] != "ok":
            continue

        for name, value in record["metrics"].items():
            values_by_metric.setdefault(name, []).append(value)

    return {name: statistics.fmean(values) for name, values in values_by_metric.items()}


def load_experiment_run(
    path: Path,
    experiment_name: str,
    configuration: dict[str, str] | None = None,
) -> ExperimentRun:
    """Build an ExperimentRun snapshot from a raw benchmark result file.

    `configuration` lets a caller record what varied between runs beyond
    provider/model (e.g. prompt version, retrieval settings) when that
    information isn't already in the result file; it defaults to just the
    provider and model already recorded by scripts/run_benchmark.py.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    run = payload["run"]
    results = payload["results"]

    resolved_configuration = {
        "llm_mode": run["llm_mode"],
        "llm_model": run["llm_model"],
        **(configuration or {}),
    }

    return ExperimentRun(
        experiment_name=experiment_name,
        git_commit=run["git_commit"],
        dataset_name=run["dataset_name"],
        dataset_version=run["dataset_version"],
        provider=run["llm_mode"],
        model=run["llm_model"],
        configuration=resolved_configuration,
        started_at=run["started_at"],
        case_ids=tuple(
            sorted(record["id"] for record in results if record["status"] == "ok")
        ),
        cases_ok=run["cases_ok"],
        cases_error=run["cases_error"],
        metrics=_metric_means(results),
        source_path=str(path),
    )
