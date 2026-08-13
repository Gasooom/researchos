"""Benchmark execution services for ResearchOS."""

from app.application.evaluation.benchmark_report import (
    BenchmarkReportBuilder,
)
from app.application.orchestration.research_agent import ResearchAgent
from app.domain.evaluation.benchmark import BenchmarkCase
from app.domain.evaluation.models import EvaluationResult
from app.domain.research.models import (
    Claim,
    Evidence,
    ResearchRequest,
    ResearchResult,
    ResearchTask,
)
from app.domain.runs.models import ResearchRunOutcome, ResearchRunStatus


class BaselineResearchRunner:
    """Run benchmark cases through a simple single-agent baseline."""

    def __init__(
        self,
        research_agent: ResearchAgent,
        report_builder: BenchmarkReportBuilder,
    ) -> None:
        self.research_agent = research_agent
        self.report_builder = report_builder

    def run(
        self,
        case: BenchmarkCase,
    ) -> tuple[ResearchResult, EvaluationResult]:
        """Run one benchmark case through the baseline system."""
        request = ResearchRequest(
            question=case.question,
            max_sources=3,
        )

        task = ResearchTask(
            objective=request.question,
            task_type="baseline",
            max_sources=request.max_sources,
        )

        evidence = self.research_agent.research(task)

        if not evidence:
            raise ValueError("baseline research returned no evidence")

        result = self._build_result(
            request=request,
            evidence=evidence,
        )

        report = self.report_builder.build(
            case=case,
            result=result,
        )

        return result, report

    @staticmethod
    def _build_result(
        request: ResearchRequest,
        evidence: list[Evidence],
    ) -> ResearchResult:
        """Build a minimal result from baseline evidence."""
        claims = [
            Claim(
                statement=evidence_item.excerpt,
                evidence=[evidence_item],
            )
            for evidence_item in evidence
        ]

        outcome = ResearchRunOutcome(
            status=ResearchRunStatus.SUCCESS,
            completed_tasks=1,
            failed_tasks=0,
            failures=[],
            evidence=evidence,
        )

        return ResearchResult(
            question=request.question,
            claims=claims,
            sources=[evidence_item.source for evidence_item in evidence],
            execution=outcome,
        )
