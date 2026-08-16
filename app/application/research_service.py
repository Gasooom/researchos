"""Application service for executing ResearchOS research use cases."""

from app.application.evaluation.claims import ClaimQualityEvaluator
from app.application.evaluation.execution import ExecutionQualityEvaluator
from app.application.evaluation.report import EvaluationReportBuilder
from app.application.evaluation.research import UnifiedResearchEvaluator
from app.application.evaluation.retrieval import RetrievalQualityEvaluator
from app.application.orchestration.research import ResearchOrchestrator
from app.domain.evaluation.models import EvaluationResult
from app.domain.research.models import ResearchRequest, ResearchResult
from app.domain.research.multi_agent import MultiAgentResearchResult
from app.domain.runs.models import ResearchRunOutcome
from app.domain.runs.observability import RunObservation


class ResearchApplicationService:
    """Expose the research workflow as application-level use cases."""

    def __init__(
        self,
        orchestrator: ResearchOrchestrator,
        evaluation_report_builder: EvaluationReportBuilder | None = None,
    ) -> None:
        self.orchestrator = orchestrator

        self.evaluation_report_builder = (
            evaluation_report_builder
            or self._create_default_evaluation_report_builder()
        )

    @staticmethod
    def _create_default_evaluation_report_builder() -> EvaluationReportBuilder:
        """Build the deterministic evaluation pipeline."""
        retrieval_evaluator = RetrievalQualityEvaluator()
        claim_quality_evaluator = ClaimQualityEvaluator()

        research_evaluator = UnifiedResearchEvaluator(
            retrieval_evaluator=retrieval_evaluator,
            claim_quality_evaluator=claim_quality_evaluator,
        )

        execution_evaluator = ExecutionQualityEvaluator()

        return EvaluationReportBuilder(
            research_evaluator=research_evaluator,
            execution_evaluator=execution_evaluator,
        )

    def execute(
        self,
        request: ResearchRequest,
    ) -> ResearchResult:
        """Execute a research request through the orchestrator."""
        return self.orchestrator.run(request)

    def execute_with_evaluation_artifacts(
        self,
        request: ResearchRequest,
    ) -> tuple[
        ResearchResult,
        ResearchRunOutcome,
        list[MultiAgentResearchResult],
    ]:
        """Execute research while preserving evaluation artifacts."""
        return self.orchestrator.run_with_evaluation_artifacts(
            request,
        )

    def execute_workspace(
        self,
        request: ResearchRequest,
    ) -> tuple[
        ResearchResult,
        ResearchRunOutcome,
        list[MultiAgentResearchResult],
        EvaluationResult,
        RunObservation | None,
    ]:
        """Execute research and assemble workspace artifacts."""
        (
            result,
            outcome,
            multi_agent_results,
        ) = self.orchestrator.run_with_evaluation_artifacts(
            request,
        )

        evaluation = self.evaluation_report_builder.build(
            result,
        )

        observation = self.orchestrator.get_last_observation()

        return (
            result,
            outcome,
            multi_agent_results,
            evaluation,
            observation,
        )
