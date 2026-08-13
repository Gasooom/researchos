from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.app import create_app
from app.domain.research.models import (
    Claim,
    Evidence,
    ResearchResult,
    Source,
)
from app.infrastructure.persistence.in_memory_run_repository import (
    InMemoryResearchRunRepository,
)


class FakeResearchService:
    """Deterministic application service for API tests."""

    def execute(self, request):
        source = Source(
            title="API Test Source",
            url="https://example.com/api-test",
            publisher="example.com",
            retrieved_at=datetime.now(UTC),
        )

        evidence = Evidence(
            source=source,
            excerpt="API test evidence.",
            relevance=0.9,
        )

        claim = Claim(
            statement="API test claim.",
            evidence=[evidence],
        )

        return ResearchResult(
            question=request.question,
            claims=[claim],
            sources=[source],
            execution=None,
        )


def build_client() -> tuple[
    TestClient,
    InMemoryResearchRunRepository,
]:
    repository = InMemoryResearchRunRepository()

    app = create_app(
        service=FakeResearchService(),
        run_repository=repository,
    )

    return TestClient(app), repository


def test_health() -> None:
    client, _ = build_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_research_endpoint() -> None:
    client, _ = build_client()

    response = client.post(
        "/research",
        json={
            "question": "How do AI agents work?",
            "max_sources": 3,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["result"]["question"] == "How do AI agents work?"
    assert len(body["result"]["claims"]) == 1
    assert len(body["result"]["sources"]) == 1


def test_research_validates_empty_question() -> None:
    client, _ = build_client()

    response = client.post(
        "/research",
        json={
            "question": "",
        },
    )

    assert response.status_code == 422


def test_run_not_found() -> None:
    client, _ = build_client()

    missing_id = UUID("00000000-0000-0000-0000-000000000001")

    response = client.get(f"/runs/{missing_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "research run not found"
