"""Domain model for a reproducible evaluation experiment run.

An `ExperimentRun` is a read-only snapshot of one completed benchmark run: it
answers "what system, on what dataset, with what configuration, produced
these metrics" without re-reading or re-aggregating the underlying result
file. It is frozen (immutable) because it describes a historical artifact
that must never be edited in place - see benchmark/README.md and M7's
overwrite guard in scripts/run_benchmark.py for the same principle applied to
the raw result files this model is built from.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExperimentRun(BaseModel):
    """Reproducibility metadata and metric snapshot for one benchmark run.

    `run_id` is derived deterministically from the fields that define
    reproducibility (dataset version, git commit, configuration, start time),
    so loading the same result file twice always yields the same identity,
    and two runs that differ in any of those respects are distinguishable.
    """

    model_config = ConfigDict(frozen=True)

    experiment_name: str = Field(min_length=1)
    git_commit: str | None
    dataset_name: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    configuration: dict[str, str] = Field(default_factory=dict)
    started_at: datetime
    case_ids: tuple[str, ...]
    cases_ok: int = Field(ge=0)
    cases_error: int = Field(ge=0)
    metrics: dict[str, float]
    source_path: str = Field(min_length=1)

    @property
    def run_id(self) -> str:
        """A stable identity derived from this run's reproducibility metadata."""
        commit = self.git_commit or "no-commit"
        config = ",".join(f"{k}={v}" for k, v in sorted(self.configuration.items()))
        return (
            f"{self.experiment_name}:{self.dataset_version}:{commit}:"
            f"{config}:{self.started_at.isoformat()}"
        )
