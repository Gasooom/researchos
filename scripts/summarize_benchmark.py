"""Summarize a benchmark results file produced by run_benchmark.py.

Reports per-metric scores, the LLM-judge score distribution, and — when a
labels file is supplied — judge-versus-human agreement computed through
HumanCalibrationService. Reads only recorded results; computes nothing it
cannot derive from them.
"""

import argparse
import json
import statistics
from pathlib import Path

from app.application.evaluation.calibration import HumanCalibrationService
from app.domain.evaluation.calibration import CalibrationLabel
from app.domain.evaluation.models import EvaluationMetric, EvaluationResult

JUDGE_METRICS = (
    "llm_groundedness",
    "llm_completeness",
    "llm_uncertainty_handling",
    "llm_judge_overall",
)

DETERMINISTIC_METRICS = (
    "overall_research_quality",
    "overall_system_quality",
    "semantic_quality",
    "focus_coverage",
    # Results recorded before the M6 rename carry the legacy names. Both are
    # reported under their own key so historical values are never relabelled
    # as something they did not measure.
    "claim_support_rate",
    "unsupported_claim_rate",
    "high_relevance_claim_rate",
    "low_relevance_claim_rate",
    "claim_evidence_overlap_rate",
    "average_relevance",
)


def describe(values: list[float]) -> dict[str, float]:
    """Summarize a sample of scores."""
    return {
        "n": len(values),
        "mean": round(statistics.fmean(values), 4),
        "median": round(statistics.median(values), 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "stdev": round(statistics.stdev(values), 4) if len(values) > 1 else 0.0,
    }


def collect(records: list[dict], metric: str) -> list[float]:
    """Gather one metric across successful records."""
    return [
        record["metrics"][metric]
        for record in records
        if record["status"] == "ok" and metric in record["metrics"]
    ]


def histogram(values: list[float], width: float = 0.05) -> dict[str, int]:
    """Bucket scores to expose the judge's score distribution."""
    buckets: dict[str, int] = {}

    for value in values:
        index = min(int(value / width), int(1 / width) - 1)
        label = f"{index * width:.2f}-{(index + 1) * width:.2f}"
        buckets[label] = buckets.get(label, 0) + 1

    return dict(sorted(buckets.items()))


def to_evaluation_result(metrics: dict[str, float]) -> EvaluationResult:
    """Rebuild the judge's evaluation result from recorded metrics."""
    return EvaluationResult(
        metrics=[
            EvaluationMetric(
                name=name,
                value=metrics[name],
                description="recorded benchmark metric",
            )
            for name in JUDGE_METRICS
        ],
        overall_score=metrics["llm_judge_overall"],
    )


def calibration_report(records: list[dict], labels_path: Path) -> dict:
    """Compare judge scores with human labels through the calibration service."""
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    by_id = {record["id"]: record for record in records if record["status"] == "ok"}
    service = HumanCalibrationService()

    dimensions = (
        ("groundedness", "llm_groundedness"),
        ("completeness", "llm_completeness"),
        ("uncertainty_handling", "llm_uncertainty_handling"),
        ("overall_score", "llm_overall_score"),
    )

    deltas: dict[str, list[float]] = {name: [] for name, _ in dimensions}
    pairs = []

    for entry in labels["labels"]:
        human_scores = entry["human"]

        if any(value is None for value in human_scores.values()):
            continue

        record = by_id.get(entry["case_id"])

        if record is None:
            continue

        calibration = service.calibrate(
            llm_result=to_evaluation_result(record["metrics"]),
            human=CalibrationLabel(**human_scores),
        )

        row = {"case_id": entry["case_id"]}

        for human_field, llm_field in dimensions:
            human_value = getattr(calibration.human, human_field)
            llm_value = getattr(calibration, llm_field)
            delta = llm_value - human_value

            deltas[human_field].append(delta)
            row[human_field] = {
                "llm": llm_value,
                "human": human_value,
                "delta": round(delta, 4),
            }

        pairs.append(row)

    if not pairs:
        return {"labeled_cases": 0, "note": "no completed human labels found"}

    summary = {}

    for name, values in deltas.items():
        absolute = [abs(value) for value in values]
        summary[name] = {
            "mean_absolute_error": round(statistics.fmean(absolute), 4),
            "mean_signed_delta": round(statistics.fmean(values), 4),
            "max_absolute_error": round(max(absolute), 4),
            "within_0.10": sum(value <= 0.10 for value in absolute),
            "within_0.20": sum(value <= 0.20 for value in absolute),
        }

    return {
        "labeled_cases": len(pairs),
        "per_dimension": summary,
        "pairs": pairs,
    }


def main() -> None:
    """Summarize a results file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path, help="path to a results json file")
    parser.add_argument("--labels", type=Path, help="path to a calibration labels file")
    parser.add_argument("--out", type=Path, help="write the summary as json")
    args = parser.parse_args()

    payload = json.loads(args.results.read_text(encoding="utf-8"))
    records = payload["results"]
    ok = [record for record in records if record["status"] == "ok"]

    summary: dict = {
        "run": payload["run"],
        "judge_metrics": {},
        "deterministic_metrics": {},
        "by_difficulty": {},
        "judge_score_distribution": {},
    }

    for metric in JUDGE_METRICS:
        values = collect(records, metric)

        if values:
            summary["judge_metrics"][metric] = describe(values)

    for metric in DETERMINISTIC_METRICS:
        values = collect(records, metric)

        if values:
            summary["deterministic_metrics"][metric] = describe(values)

    overall = collect(records, "llm_judge_overall")

    if overall:
        summary["judge_score_distribution"] = histogram(overall)

    for difficulty in ("easy", "moderate", "hard"):
        subset = [record for record in ok if record["difficulty"] == difficulty]

        if not subset:
            continue

        summary["by_difficulty"][difficulty] = {
            metric: describe(collect(subset, metric))
            for metric in JUDGE_METRICS
            if collect(subset, metric)
        }

    uncertain = [record for record in ok if record["uncertainty_expected"]]
    certain = [record for record in ok if not record["uncertainty_expected"]]

    if uncertain and certain:
        summary["uncertainty_handling_split"] = {
            "uncertainty_expected": describe(
                collect(uncertain, "llm_uncertainty_handling")
            ),
            "uncertainty_not_expected": describe(
                collect(certain, "llm_uncertainty_handling")
            ),
        }

    if args.labels:
        summary["calibration"] = calibration_report(records, args.labels)

    print(json.dumps(summary, indent=2))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
