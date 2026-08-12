from datetime import UTC, datetime

from app.application.agents.contracts import SpecializedResearchAgent
from app.application.agents.roles import AgentRole
from app.domain.research.models import Evidence, ResearchTask, Source


class RetrievalAgent:
    """Minimal retrieval agent used to verify the contract."""

    @property
    def role(self) -> AgentRole:
        return AgentRole.RETRIEVAL

    def execute(self, task: ResearchTask) -> list[Evidence]:
        source = Source(
            title="Example Research",
            url="https://example.com/research",
            publisher="Example",
            retrieved_at=datetime.now(UTC),
        )

        return [
            Evidence(
                source=source,
                excerpt=f"Evidence for: {task.objective}",
                relevance=0.9,
            )
        ]


def test_specialized_agent_contract() -> None:
    agent: SpecializedResearchAgent = RetrievalAgent()

    task = ResearchTask(
        objective="Investigate AI agent reliability.",
    )

    assert agent.role == AgentRole.RETRIEVAL

    evidence = agent.execute(task)

    assert len(evidence) == 1
    assert evidence[0].relevance == 0.9
