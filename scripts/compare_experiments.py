"""Compare two benchmark result files as experiment runs, without modifying
either.

Thin CLI over app.application.experiments. Unlike scripts/compare_benchmarks.py,
this has no ResearchOS-specific knowledge of what changed between runs (e.g.
the M6 claim-independence rename) - it just diffs whatever metric names two
runs share and says plainly when one is missing on either side.
"""

import argparse
from pathlib import Path

from app.application.experiments.comparison import (
    IncompatibleExperiments,
    compare_experiment_runs,
)
from app.application.experiments.loader import load_experiment_run


def main() -> None:
    """Load two result files as experiment runs and compare them."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument(
        "--experiment-name",
        default="researchos-benchmark",
        help="logical experiment these runs belong to (default: %(default)s)",
    )
    parser.add_argument("--out", type=Path, help="write the comparison as json")
    args = parser.parse_args()

    baseline = load_experiment_run(args.baseline, args.experiment_name)
    candidate = load_experiment_run(args.candidate, args.experiment_name)

    try:
        comparison = compare_experiment_runs(baseline, candidate)
    except IncompatibleExperiments as exc:
        raise SystemExit(f"refusing to compare: {exc}") from exc

    print(f"baseline : {baseline.run_id}")
    print(f"candidate: {candidate.run_id}\n")

    for row in comparison.metrics:
        base = "n/a" if row.baseline is None else f"{row.baseline:.4f}"
        cand = "n/a" if row.candidate is None else f"{row.candidate:.4f}"
        delta = "" if row.delta is None else f"  delta {row.delta:+.4f}"
        flag = "" if row.status == "compared" else f"  [{row.status}]"

        print(f"  {row.metric:<40} {base:>8} -> {cand:>8}{delta}{flag}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            comparison.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
