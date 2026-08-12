from app.core.models.research import ResearchTask
from app.core.services.agent_roles import AgentRole
from app.core.services.retrieval_agent import RetrievalAgent


class StubSearchProvider:
    """Deterministic search provider for retrieval-agent tests."""

    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str) -> list[dict[str, str | float]]:
        self.queries.append(query)

        return [
            {
                "title": "AI Reliability Research",
                "url": "https://example.com/reliability",
                "publisher": "example.com",
                "excerpt": "AI agents can fail unpredictably.",
                "relevance": 0.92,
            },
            {
                "title": "Agent Evaluation",
                "url": "https://example.com/evaluation",
                "publisher": "example.com",
                "excerpt": "Evaluation improves agent reliability.",
                "relevance": 0.81,
            },
            {
                "title": "Extra Source",
                "url": "https://example.com/extra",
                "publisher": "example.com",
                "excerpt": "Additional evidence.",
                "relevance": 0.70,
            },
        ]


def test_retrieval_agent_has_retrieval_role() -> None:
    provider = StubSearchProvider()
    agent = RetrievalAgent(provider)

    assert agent.role == AgentRole.RETRIEVAL


def test_retrieval_agent_returns_evidence() -> None:
    provider = StubSearchProvider()
    agent = RetrievalAgent(provider)

    task = ResearchTask(
        objective="Investigate AI agent reliability.",
        max_sources=2,
    )

    evidence = agent.execute(task)

    assert len(evidence) == 2
    assert evidence[0].source.title == "AI Reliability Research"
    assert str(evidence[0].source.url) == ("https://example.com/reliability")
    assert evidence[0].excerpt == "AI agents can fail unpredictably."
    assert evidence[0].relevance == 0.92
    assert evidence[0].source.retrieved_at.tzinfo is not None


def test_retrieval_agent_uses_task_objective_as_query() -> None:
    provider = StubSearchProvider()
    agent = RetrievalAgent(provider)

    task = ResearchTask(
        objective="Investigate AI agent reliability.",
        max_sources=2,
    )

    agent.execute(task)

    assert provider.queries == [
        "Investigate AI agent reliability.",
    ]


def test_retrieval_agent_respects_max_sources() -> None:
    provider = StubSearchProvider()
    agent = RetrievalAgent(provider)

    task = ResearchTask(
        objective="Investigate AI agent reliability.",
        max_sources=1,
    )

    evidence = agent.execute(task)

    assert len(evidence) == 1
