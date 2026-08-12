"""Research orchestration services for ResearchOS."""

from app.application.claims.grounder import ClaimGrounder
from app.application.claims.support_classifier import (
    ClaimSupportClassifier,
)
from app.application.evidence.extractor import EvidenceExtractor
from app.application.orchestration.multi_agent import MultiAgentCoordinator
from app.application.orchestration.planning import PlannerStrategy
from app.application.orchestration.run_executor import ResearchRunExecutor
from app.application.retrieval.collector import SourceCollector
from app.application.retrieval.deduplicator import SourceDeduplicator
from app.application.retrieval.selector import SourceSelector
from app.application.review.router import ClaimReviewRouter
from app.domain.research.models import (
    Claim,
    Evidence,
    ResearchRequest,
    ResearchResult,
)
from app.domain.runs.models import (
    ResearchRunFailure,
    ResearchRunOutcome,
    ResearchRunStatus,
)


class ResearchOrchestrator:
    """Coordinate planning, execution, evidence, and claim construction."""

    def __init__(
        self,
        planner: PlannerStrategy,
        run_executor: ResearchRunExecutor,
        source_collector: SourceCollector,
        source_deduplicator: SourceDeduplicator,
        source_selector: SourceSelector,
        evidence_extractor: EvidenceExtractor,
        claim_grounder: ClaimGrounder,
        claim_support_classifier: ClaimSupportClassifier,
        claim_review_router: ClaimReviewRouter,
        multi_agent_coordinator: MultiAgentCoordinator | None = None,
    ) -> None:
        self.planner = planner
        self.run_executor = run_executor
        self.source_collector = source_collector
        self.source_deduplicator = source_deduplicator
        self.source_selector = source_selector
        self.evidence_extractor = evidence_extractor
        self.claim_grounder = claim_grounder
        self.claim_support_classifier = claim_support_classifier
        self.claim_review_router = claim_review_router
        self.multi_agent_coordinator = multi_agent_coordinator

    def run(self, request: ResearchRequest) -> ResearchResult:
        """Execute a complete research workflow."""
        tasks = self.planner.plan(request)

        if self.multi_agent_coordinator is not None:
            return self._run_multi_agent(request, tasks)

        outcome = self.run_executor.execute(tasks)

        return self._build_result(
            request=request,
            all_evidence=outcome.evidence,
            execution=outcome,
        )

    def _run_multi_agent(
        self,
        request: ResearchRequest,
        tasks: list,
    ) -> ResearchResult:
        """Execute all planned tasks through the multi-agent coordinator."""
        if not tasks:
            raise ValueError("planner returned no research tasks")

        all_evidence: list[Evidence] = []
        failures: list[ResearchRunFailure] = []
        completed_tasks = 0

        for task in tasks:
            try:
                result = self.multi_agent_coordinator.execute(task)
                all_evidence.extend(result.evidence)
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

        execution = ResearchRunOutcome(
            status=status,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            failures=failures,
            evidence=all_evidence,
        )

        if not all_evidence:
            raise ValueError("multi-agent execution returned no evidence")

        return self._build_result(
            request=request,
            all_evidence=all_evidence,
            execution=execution,
        )

    def _build_result(
        self,
        request: ResearchRequest,
        all_evidence: list[Evidence],
        execution: ResearchRunOutcome,
    ) -> ResearchResult:
        """Build sources, claims, and the final research result."""
        source_results = [
            {
                "title": evidence.source.title,
                "url": str(evidence.source.url),
                "publisher": evidence.source.publisher,
                "excerpt": evidence.excerpt,
                "relevance": evidence.relevance,
            }
            for evidence in all_evidence
        ]

        sources = self.source_collector.collect(source_results)
        sources = self.source_deduplicator.deduplicate(sources)
        sources = self.source_selector.select(sources)

        claims: list[Claim] = []

        for evidence in all_evidence:
            evidence_record = self.evidence_extractor.extract(
                source=evidence.source,
                content=evidence.excerpt,
                relevance=evidence.relevance,
            )

            claim = self.claim_grounder.ground(
                statement=evidence_record.excerpt,
                evidence=[evidence_record],
            )

            self.claim_support_classifier.classify(claim)
            self.claim_review_router.route(claim)

            claims.append(claim)

        return ResearchResult(
            question=request.question,
            claims=claims,
            sources=sources,
            execution=execution,
        )
