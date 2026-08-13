"""Research orchestration services for ResearchOS."""

from datetime import UTC, datetime

from app.application.claims.grounder import ClaimGrounder
from app.application.claims.support_classifier import ClaimSupportClassifier
from app.application.evidence.extractor import EvidenceExtractor
from app.application.orchestration.multi_agent import MultiAgentCoordinator
from app.application.orchestration.planning import PlannerStrategy
from app.application.orchestration.run_executor import ResearchRunExecutor
from app.application.retrieval.collector import SourceCollector
from app.application.retrieval.deduplicator import SourceDeduplicator
from app.application.retrieval.selector import SourceSelector
from app.application.retrieval.verifier import SourceVerifier
from app.application.review.router import ClaimReviewRouter
from app.domain.research.models import (
    Claim,
    Evidence,
    ResearchRequest,
    ResearchResult,
)
from app.domain.research.multi_agent import MultiAgentResearchResult
from app.domain.runs.models import (
    ResearchRunFailure,
    ResearchRunOutcome,
    ResearchRunStatus,
)
from app.domain.runs.record import ResearchRunRecord
from app.domain.runs.repository import ResearchRunRepository
from app.infrastructure.telemetry.run_observer import RunObserver


class ResearchOrchestrator:
    """Coordinate planning, execution, persistence, and observability."""

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
        source_verifier: SourceVerifier | None = None,
        multi_agent_coordinator: MultiAgentCoordinator | None = None,
        run_repository: ResearchRunRepository | None = None,
        run_observer: RunObserver | None = None,
        memory_service=None,
    ) -> None:
        self.planner = planner
        self.run_executor = run_executor
        self.source_collector = source_collector
        self.source_deduplicator = source_deduplicator
        self.source_selector = source_selector
        self.source_verifier = source_verifier or SourceVerifier()
        self.evidence_extractor = evidence_extractor
        self.claim_grounder = claim_grounder
        self.claim_support_classifier = claim_support_classifier
        self.claim_review_router = claim_review_router
        self.multi_agent_coordinator = multi_agent_coordinator
        self.run_repository = run_repository
        self.run_observer = run_observer
        self.memory_service = memory_service

    def run(self, request: ResearchRequest) -> ResearchResult:
        """Execute a complete research workflow."""
        result, _, _ = self.run_with_evaluation_artifacts(request)

        return result

    def run_with_evaluation_artifacts(
        self,
        request: ResearchRequest,
    ) -> tuple[
        ResearchResult,
        ResearchRunOutcome,
        list[MultiAgentResearchResult],
    ]:
        """Execute research while preserving evaluation artifacts."""
        started_at = datetime.now(UTC)

        if self.memory_service is not None:
            self.memory_service.retrieve(
                question=request.question,
            )

        tasks = self.planner.plan(request)

        multi_agent_results: list[MultiAgentResearchResult] = []

        if self.multi_agent_coordinator is not None:
            (
                result,
                outcome,
                multi_agent_results,
            ) = self._run_multi_agent(
                request=request,
                tasks=tasks,
            )
        else:
            outcome = self.run_executor.execute(tasks)

            result = self._build_result(
                request=request,
                all_evidence=outcome.evidence,
                execution=outcome,
            )

        if self.memory_service is not None:
            self.memory_service.store(result)

        self._persist_run(
            started_at=started_at,
            outcome=outcome,
        )

        return (
            result,
            outcome,
            multi_agent_results,
        )

    def _persist_run(
        self,
        started_at: datetime,
        outcome: ResearchRunOutcome,
    ) -> None:
        """Persist a completed run and its operational observation."""
        if self.run_repository is None:
            return

        completed_at = datetime.now(UTC)
        duration_seconds = (completed_at - started_at).total_seconds()

        observation = None

        if self.run_observer is not None:
            observation = self.run_observer.observe(
                outcome=outcome,
                duration_seconds=duration_seconds,
            )

        self.run_repository.save(
            ResearchRunRecord(
                created_at=started_at,
                completed_at=completed_at,
                outcome=outcome,
                observation=observation,
            )
        )

    def _run_multi_agent(
        self,
        request: ResearchRequest,
        tasks: list,
    ) -> tuple[
        ResearchResult,
        ResearchRunOutcome,
        list[MultiAgentResearchResult],
    ]:
        """Execute all planned tasks through the multi-agent coordinator."""
        if not tasks:
            raise ValueError("planner returned no research tasks")

        all_evidence: list[Evidence] = []
        failures: list[ResearchRunFailure] = []
        multi_agent_results: list[MultiAgentResearchResult] = []
        completed_tasks = 0

        for task in tasks:
            try:
                agent_result = self.multi_agent_coordinator.execute(
                    task,
                )

                multi_agent_results.append(agent_result)
                all_evidence.extend(agent_result.evidence)
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

        outcome = ResearchRunOutcome(
            status=status,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            failures=failures,
            evidence=all_evidence,
        )

        if not all_evidence:
            raise ValueError(
                "multi-agent execution returned no evidence",
            )

        research_result = self._build_result(
            request=request,
            all_evidence=all_evidence,
            execution=outcome,
        )

        return (
            research_result,
            outcome,
            multi_agent_results,
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

        sources = self.source_collector.collect(
            source_results,
        )

        sources = self.source_deduplicator.deduplicate(
            sources,
        )

        sources = self.source_selector.select(
            sources,
        )

        verified_sources = []

        for source in sources:
            verification = self.source_verifier.verify(source)

            if verification.status.value == "verified":
                verified_sources.append(source)

        sources = verified_sources

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

            self.claim_support_classifier.classify(
                claim,
            )

            self.claim_review_router.route(
                claim,
            )

            claims.append(claim)

        return ResearchResult(
            question=request.question,
            claims=claims,
            sources=sources,
            execution=execution,
        )
