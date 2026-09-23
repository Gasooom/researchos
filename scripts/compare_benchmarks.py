"""Compare two benchmark result files without modifying either.

Thin CLI over app.application.evaluation.comparison.
"""

import argparse
import json
from pathlib import Path

from app.application.evaluation.comparison import (
    IncompatibleBenchmarks,
    build_comparison,
)


def print_group(title: str, rows: list[dict], note: str = "") -> None:
    """Render one metric group."""
    print(f"\n=== {title} ===")

    if note:
        print(note)

    if not rows:
        print("  (none)")
        return

    for row in rows:
        base = "n/a" if row["baseline"] is None else f"{row['baseline']:.4f}"
        cand = "n/a" if row["candidate"] is None else f"{row['candidate']:.4f}"
        delta = "" if row["delta"] is None else f"  delta {row['delta']:+.4f}"

        print(f"  {row['metric']:<44} {base:>8} -> {cand:>8}{delta}")


def main() -> None:
    """Compare two benchmark runs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--out", type=Path, help="write the comparison as json")
    args = parser.parse_args()

    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))

    try:
        comparison = build_comparison(baseline, candidate)
    except IncompatibleBenchmarks as exc:
        raise SystemExit(f"refusing to compare: {exc}") from exc

    base_commit = comparison["baseline"]["git_commit"]
    cand_commit = comparison["candidate"]["git_commit"]

    print(f"baseline : {args.baseline.name}  ({base_commit})")
    print(f"candidate: {args.candidate.name}  ({cand_commit})")

    print_group("comparable", comparison["comparable"])
    print_group(
        "renamed - same formula, different claim population",
        comparison["renamed_population_changed"],
        "Deltas here are structural, not improvements.",
    )
    print_group(
        "claim evidence population changed - deltas are NOT improvements",
        comparison["claim_population_changed"],
        "These iterate claim.evidence, whose contents M6 changed.",
    )
    print_group(
        "claim text changed - deltas are NOT improvements",
        comparison["claim_text_changed"],
        "These read claim.statement, which M6 redefined.",
    )
    print_group(
        "composite scores - mix both effects, deltas are NOT improvements",
        comparison["composite_changed"],
    )
    print_group("new in candidate", comparison["new_in_candidate"])

    print(f"\n{comparison['interpretation']}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(comparison, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
