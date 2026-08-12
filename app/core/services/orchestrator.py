"""Research orchestration services for ResearchOS."""

from app.core.models.research import Claim, ResearchRequest, ResearchResult
from app.core.services.claim_grounder import ClaimGrounder
from app.core.services.claim_review import ClaimReviewRouter
from app.core.services.claim_support_classifier import (
    ClaimSupportClassifier,
)
from app.core.services.evidence_extractor import EvidenceExtractor
from app.core.services.planning import PlannerStrategy
from app.core.services.run_executor import ResearchRunExecutor
from app.core.services.source_collector import SourceCollector
from app.core.services.source_deduplicator import SourceDeduplicator
from app.core.services.source_selector import SourceSelector


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

    def run(self, request: ResearchRequest) -> ResearchResult:
        """Execute a complete research workflow."""
        tasks = self.planner.plan(request)
        outcome = self.run_executor.execute(tasks)

        all_evidence = outcome.evidence

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
        )
