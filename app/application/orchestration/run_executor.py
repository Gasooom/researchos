"""Research run execution services for ResearchOS."""

from app.application.orchestration.reliable_agent import ReliableResearchAgent
from app.domain.research.models import Evidence, ResearchTask
from app.domain.runs.models import (
    ResearchRunFailure,
    ResearchRunOutcome,
    ResearchRunStatus,
)


class ResearchRunExecutor:
    """Execute research tasks while preserving partial results."""

    def __init__(self, research_agent: ReliableResearchAgent) -> None:
        self.research_agent = research_agent

    def execute(
        self,
        tasks: list[ResearchTask],
    ) -> ResearchRunOutcome:
        """Execute all tasks and preserve successful evidence."""
        completed_tasks = 0
        failures: list[ResearchRunFailure] = []
        evidence: list[Evidence] = []

        for task in tasks:
            try:
                task_evidence = self.research_agent.research(task)
                evidence.extend(task_evidence)
                completed_tasks += 1
            except Exception as exc:
                failures.append(
                    ResearchRunFailure(
                        task_objective=task.objective,
                        error_type=type(exc).__name__,
                        message=str(exc),
                    )
                )

        failed_tasks = len(failures)

        if failed_tasks == 0:
            status = ResearchRunStatus.SUCCESS
        elif completed_tasks == 0:
            status = ResearchRunStatus.FAILED
        else:
            status = ResearchRunStatus.PARTIAL

        return ResearchRunOutcome(
            status=status,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            failures=failures,
            evidence=evidence,
        )
