"""Execute the versioned ResearchOS benchmark against the live system.

Writes raw per-case results to benchmark/results/<date>.json. Every number in
that file comes from an actual run; failures are recorded as failures.
"""

import argparse
import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from app.application.evaluation.benchmark_dataset import (
    BenchmarkCaseSpec,
    load_benchmark_dataset,
)
from app.application.evaluation.benchmark_report import BenchmarkReportBuilder
from app.application.evaluation.claims import ClaimQualityEvaluator
from app.application.evaluation.execution import ExecutionQualityEvaluator
from app.application.evaluation.llm_judge import LLMJudgeEvaluator
from app.application.evaluation.report import EvaluationReportBuilder
from app.application.evaluation.research import UnifiedResearchEvaluator
from app.application.evaluation.researchos_benchmark import (
    ResearchOSBenchmarkRunner,
)
from app.application.evaluation.retrieval import RetrievalQualityEvaluator
from app.application.evaluation.semantic import SemanticQualityEvaluator
from app.bootstrap.container import create_research_service
from app.core.config import get_settings
from app.domain.evaluation.models import EvaluationResult
from app.infrastructure.llm.factory import create_llm_provider

RESULTS_DIR = Path(__file__).resolve().parents[1] / "benchmark" / "results"


def build_runner() -> ResearchOSBenchmarkRunner:
    """Wire the production service to a judge-backed benchmark report builder."""
    settings = get_settings()

    if settings.llm_mode != "openai":
        raise SystemExit(
            f"LLM_MODE is '{settings.llm_mode}'; live benchmark requires 'openai'."
        )

    service = create_research_service(settings)

    report_builder = BenchmarkReportBuilder(
        report_builder=EvaluationReportBuilder(
            research_evaluator=UnifiedResearchEvaluator(
                retrieval_evaluator=RetrievalQualityEvaluator(),
                claim_quality_evaluator=ClaimQualityEvaluator(),
            ),
            execution_evaluator=ExecutionQualityEvaluator(),
            llm_judge=LLMJudgeEvaluator(
                provider=create_llm_provider(settings),
            ),
        ),
        semantic_evaluator=SemanticQualityEvaluator(),
    )

    return ResearchOSBenchmarkRunner(
        service=service,
        report_builder=report_builder,
    )


def metrics_to_dict(report: EvaluationResult) -> dict[str, float]:
    """Flatten evaluation metrics into a name to value mapping."""
    return {metric.name: metric.value for metric in report.metrics}


def run_case(
    runner: ResearchOSBenchmarkRunner,
    spec: BenchmarkCaseSpec,
) -> dict:
    """Run one case, recording either its metrics or its failure."""
    record: dict = {
        "id": spec.id,
        "question": spec.question,
        "difficulty": spec.difficulty,
        "domain": spec.domain,
        "uncertainty_expected": spec.uncertainty_expected,
    }

    started = time.monotonic()

    try:
        execution, report = runner.run(spec.to_case())
    except Exception as exc:
        record.update(
            status="error",
            error_type=type(exc).__name__,
            error=str(exc),
            duration_seconds=round(time.monotonic() - started, 2),
        )

        return record

    outcome = execution.result.execution

    record.update(
        status="ok",
        duration_seconds=round(time.monotonic() - started, 2),
        execution_status=outcome.status.value,
        completed_tasks=outcome.completed_tasks,
        failed_tasks=outcome.failed_tasks,
        claim_count=len(execution.result.claims),
        source_count=len(execution.result.sources),
        multi_agent_result_count=len(execution.multi_agent_results),
        overall_score=report.overall_score,
        metrics=metrics_to_dict(report),
        claims=[claim.statement for claim in execution.result.claims],
        sources=[
            {
                "title": source.title,
                "url": str(source.url),
                "publisher": source.publisher,
            }
            for source in execution.result.sources
        ],
    )

    return record


def git_commit() -> str | None:
    """Return the current commit, so results stay traceable to code."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def write_results(
    out_path: Path,
    records: list[dict],
    started_at: datetime,
    settings,
    dataset,
) -> dict:
    """Write results after every case so an interruption cannot lose the run."""
    completed_at = datetime.now(UTC)

    payload = {
        "run": {
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": round(
                (completed_at - started_at).total_seconds(),
                2,
            ),
            "git_commit": git_commit(),
            "llm_model": settings.llm_model,
            "llm_mode": settings.llm_mode,
            "dataset_name": dataset.name,
            "dataset_version": dataset.version,
            "cases_recorded": len(records),
            "cases_ok": sum(record["status"] == "ok" for record in records),
            "cases_error": sum(record["status"] == "error" for record in records),
        },
        "results": records,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    return payload


def main() -> None:
    """Run the benchmark and write raw results."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        help="run only the first N cases",
    )
    parser.add_argument(
        "--cases",
        help="comma-separated case ids to run",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="output path (default: benchmark/results/<date>.json)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="skip cases already recorded as ok in the output file",
    )
    args = parser.parse_args()

    dataset = load_benchmark_dataset()
    specs = list(dataset.cases)

    if args.cases:
        wanted = {value.strip() for value in args.cases.split(",")}
        index = dataset.cases_by_id()
        missing = wanted - index.keys()

        if missing:
            raise SystemExit(f"unknown case ids: {sorted(missing)}")

        specs = [index[case_id] for case_id in wanted]

    if args.limit:
        specs = specs[: args.limit]

    settings = get_settings()
    started_at = datetime.now(UTC)
    out_path = args.out or RESULTS_DIR / f"{started_at.date().isoformat()}.json"

    records = []

    if out_path.exists() and not args.resume:
        raise SystemExit(
            f"{out_path} already exists. Committed results are historical "
            "artifacts and must not be overwritten: pass --out with a new path, "
            "or --resume to continue that run."
        )

    if args.resume and out_path.exists():
        previous = json.loads(out_path.read_text(encoding="utf-8"))
        records = [r for r in previous["results"] if r["status"] == "ok"]
        done = {record["id"] for record in records}
        specs = [spec for spec in specs if spec.id not in done]
        print(f"Resuming: {len(done)} case(s) already recorded", flush=True)

    runner = build_runner()

    print(f"Running {len(specs)} case(s) against {settings.llm_model}", flush=True)

    for position, spec in enumerate(specs, start=1):
        print(f"[{position}/{len(specs)}] {spec.id} ...", end=" ", flush=True)

        record = run_case(runner, spec)
        records.append(record)

        write_results(out_path, records, started_at, settings, dataset)

        if record["status"] == "ok":
            judge = record["metrics"].get("llm_judge_overall")
            judge_text = f"judge={judge:.2f}" if judge is not None else "judge=n/a"
            print(
                f"{record['execution_status']} "
                f"{judge_text} ({record['duration_seconds']}s)",
                flush=True,
            )
        else:
            print(f"ERROR {record['error_type']}: {record['error'][:80]}", flush=True)

    payload = write_results(out_path, records, started_at, settings, dataset)

    print(f"\nWrote {out_path}")
    print(
        f"ok={payload['run']['cases_ok']} "
        f"error={payload['run']['cases_error']} "
        f"in {payload['run']['duration_seconds']}s"
    )


if __name__ == "__main__":
    main()
