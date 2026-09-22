"""Build a calibration labeling file from a benchmark results file.

Selects a subset spanning all difficulty tiers and emits each case's rubric
alongside the actual system output, so labels are assigned against what the
system really produced. Draft and human score fields are left null: the draft
is filled in by review of the output, the human fields by the repository owner.
"""

import argparse
import json
from pathlib import Path

from app.application.evaluation.benchmark_dataset import load_benchmark_dataset

EMPTY_LABEL = {
    "groundedness": None,
    "completeness": None,
    "uncertainty_handling": None,
    "overall_score": None,
}

DEFAULT_QUOTA = {"easy": 3, "moderate": 3, "hard": 2}


def select(records: list[dict], quota: dict[str, int]) -> list[dict]:
    """Pick cases spread evenly through each difficulty tier."""
    chosen: list[dict] = []

    for difficulty, wanted in quota.items():
        tier = [
            record
            for record in records
            if record["status"] == "ok" and record["difficulty"] == difficulty
        ]

        if not tier:
            continue

        step = max(len(tier) // wanted, 1)
        chosen.extend(tier[::step][:wanted])

    return chosen


def main() -> None:
    """Emit the labeling file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, help="path to a results json file")
    parser.add_argument("--out", type=Path, required=True, help="labels file to write")
    args = parser.parse_args()

    payload = json.loads(args.results.read_text(encoding="utf-8"))
    specs = load_benchmark_dataset().cases_by_id()

    selected = select(payload["results"], DEFAULT_QUOTA)

    labels = []

    for record in selected:
        spec = specs[record["id"]]

        labels.append(
            {
                "case_id": record["id"],
                "question": record["question"],
                "difficulty": record["difficulty"],
                "uncertainty_expected": record["uncertainty_expected"],
                "rubric": {
                    "must_contain": spec.must_contain,
                    "must_avoid": spec.must_avoid,
                },
                "system_output": {
                    "claims": record["claims"],
                    "sources": record["sources"],
                },
                "judge_scores": {
                    name: record["metrics"][name]
                    for name in (
                        "llm_groundedness",
                        "llm_completeness",
                        "llm_uncertainty_handling",
                        "llm_judge_overall",
                    )
                    if name in record["metrics"]
                },
                "draft": dict(EMPTY_LABEL),
                "draft_reasoning": None,
                "human": dict(EMPTY_LABEL),
            }
        )

    out = {
        "source_results": args.results.name,
        "dataset_version": payload["run"]["dataset_version"],
        "git_commit": payload["run"]["git_commit"],
        "label_scale": (
            "0.0-1.0 per dimension, judged against the case rubric and the "
            "system output shown, not against an ideal answer"
        ),
        "provenance": (
            "draft = rubric-applied pre-annotation; human = repository owner's "
            "reviewed judgment. Agreement is computed from the human fields."
        ),
        "labels": labels,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {args.out} with {len(labels)} cases")

    for entry in labels:
        print(f"  {entry['difficulty']:8} {entry['case_id']}")


if __name__ == "__main__":
    main()
