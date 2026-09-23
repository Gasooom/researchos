import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.application.experiments.loader import load_experiment_run

RUN = {
    "started_at": "2026-09-22T15:57:22.625179+00:00",
    "completed_at": "2026-09-22T17:12:38.273123+00:00",
    "duration_seconds": 4515.65,
    "git_commit": "abc123",
    "llm_model": "gpt-5-mini",
    "llm_mode": "openai",
    "dataset_name": "researchos-benchmark",
    "dataset_version": "1.0.0",
    "cases_recorded": 2,
    "cases_ok": 2,
    "cases_error": 0,
}


def write_result(path: Path, results: list[dict], run: dict | None = None) -> Path:
    payload = {"run": run or RUN, "results": results}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_loader_captures_reproducibility_metadata(tmp_path: Path) -> None:
    path = write_result(
        tmp_path / "result.json",
        [
            {"id": "case-a", "status": "ok", "metrics": {"average_relevance": 0.9}},
            {"id": "case-b", "status": "ok", "metrics": {"average_relevance": 0.7}},
        ],
    )

    run = load_experiment_run(path, experiment_name="researchos-benchmark")

    assert run.git_commit == "abc123"
    assert run.dataset_version == "1.0.0"
    assert run.provider == "openai"
    assert run.model == "gpt-5-mini"
    assert run.configuration == {"llm_mode": "openai", "llm_model": "gpt-5-mini"}
    assert run.started_at.isoformat() == "2026-09-22T15:57:22.625179+00:00"
    assert run.case_ids == ("case-a", "case-b")


def test_loader_averages_each_metric_over_cases_that_report_it(
    tmp_path: Path,
) -> None:
    """A metric only some cases report must not be treated as zero elsewhere."""
    path = write_result(
        tmp_path / "result.json",
        [
            {
                "id": "case-a",
                "status": "ok",
                "metrics": {"average_relevance": 1.0, "only_case_a": 0.4},
            },
            {"id": "case-b", "status": "ok", "metrics": {"average_relevance": 0.5}},
            {"id": "case-c", "status": "error", "metrics": {}},
        ],
    )

    run = load_experiment_run(path, experiment_name="researchos-benchmark")

    assert run.metrics["average_relevance"] == pytest.approx(0.75)
    assert run.metrics["only_case_a"] == pytest.approx(0.4)
    assert run.case_ids == ("case-a", "case-b")


def test_loader_does_not_write_to_the_result_file(tmp_path: Path) -> None:
    path = write_result(
        tmp_path / "result.json",
        [{"id": "case-a", "status": "ok", "metrics": {"average_relevance": 0.9}}],
    )
    before = path.read_bytes()

    load_experiment_run(path, experiment_name="researchos-benchmark")

    assert path.read_bytes() == before


def test_experiment_run_is_frozen(tmp_path: Path) -> None:
    path = write_result(
        tmp_path / "result.json",
        [{"id": "case-a", "status": "ok", "metrics": {"average_relevance": 0.9}}],
    )
    run = load_experiment_run(path, experiment_name="researchos-benchmark")

    with pytest.raises(ValidationError):
        run.dataset_version = "9.9.9"


def test_caller_supplied_configuration_extends_provider_and_model(
    tmp_path: Path,
) -> None:
    path = write_result(
        tmp_path / "result.json",
        [{"id": "case-a", "status": "ok", "metrics": {"average_relevance": 0.9}}],
    )

    run = load_experiment_run(
        path,
        experiment_name="researchos-benchmark",
        configuration={"prompt_version": "v2"},
    )

    assert run.configuration == {
        "llm_mode": "openai",
        "llm_model": "gpt-5-mini",
        "prompt_version": "v2",
    }
