from app.core.services.agent_roles import AgentRole


def test_agent_roles_are_explicit() -> None:
    assert AgentRole.RETRIEVAL.value == "retrieval"
    assert AgentRole.ANALYSIS.value == "analysis"
    assert AgentRole.SYNTHESIS.value == "synthesis"
