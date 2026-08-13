from datetime import UTC, datetime
from unittest.mock import Mock

from app.application.orchestration.research import ResearchOrchestrator
from app.application.research_service import ResearchApplicationService
from app.domain.research.models import (
    Claim,
    Evidence,
    ResearchRequest,
    ResearchResult,
    Source,
)


def make_result() -> ResearchResult:
    source = Source(
        title="Example Research",
        url="https://example.com/research",
        publisher="Example Research",
        retrieved_at=datetime.now(UTC),
    )

    evidence = Evidence(
        source=source,
        excerpt="AI agents benefit from evaluation.",
        relevance=0.9,
    )

    claim = Claim(
        statement="AI agents benefit from evaluation.",
        evidence=[evidence],
    )

    return ResearchResult(
        question="What improves AI agent reliability?",
        claims=[claim],
        sources=[source],
        execution=None,
    )


def test_application_service_delegates_to_orchestrator() -> None:
    orchestrator = Mock(spec=ResearchOrchestrator)

    expected_result = make_result()
    orchestrator.run.return_value = expected_result

    service = ResearchApplicationService(orchestrator)

    request = ResearchRequest(question="What improves AI agent reliability?")

    result = service.execute(request)

    assert result == expected_result
    orchestrator.run.assert_called_once_with(request)
