from datetime import UTC, datetime

from app.application.orchestration.multi_agent import MultiAgentCoordinator
from app.domain.research.analysis import AnalysisResult
from app.domain.research.models import Evidence, ResearchTask, Source
from app.domain.research.synthesis import SynthesisResult


class StubRetrievalAgent:
    """Deterministic retrieval agent for coordinator tests."""

    def __init__(self) -> None:
        self.tasks: list[str] = []

    def execute(self, task: ResearchTask) -> list[Evidence]:
        self.tasks.append(task.objective)

        source = Source(
            title="Example Research",
            url="https://example.com/research",
            publisher="Example Research",
            retrieved_at=datetime.now(UTC),
        )

        return [
            Evidence(
                source=source,
                excerpt="AI agents can fail unpredictably.",
                relevance=0.92,
            )
        ]


class StubAnalysisAgent:
    """Deterministic analysis agent for coordinator tests."""

    def __init__(self) -> None:
        self.received_evidence: list[Evidence] = []

    def execute(
        self,
        task: ResearchTask,
        evidence: list[Evidence],
    ) -> AnalysisResult:
        self.received_evidence = evidence

        return AnalysisResult(
            summary="AI agents require careful evaluation.",
            key_points=[
                "AI agents can fail unpredictably.",
            ],
            confidence=0.92,
        )


class StubSynthesisAgent:
    """Deterministic synthesis agent for coordinator tests."""

    def __init__(self) -> None:
        self.received_analysis: AnalysisResult | None = None
        self.received_evidence: list[Evidence] = []

    def execute(
        self,
        task: ResearchTask,
        evidence: list[Evidence],
        analysis: AnalysisResult,
    ) -> SynthesisResult:
        self.received_evidence = evidence
        self.received_analysis = analysis

        return SynthesisResult(
            answer="AI agents require careful evaluation.",
            supporting_points=[
                "AI agents can fail unpredictably.",
            ],
            confidence=0.92,
        )


def make_task() -> ResearchTask:
    return ResearchTask(
        objective="Investigate AI agent reliability.",
        task_type="research",
        max_sources=3,
    )


def build_coordinator() -> tuple[
    MultiAgentCoordinator,
    StubRetrievalAgent,
    StubAnalysisAgent,
    StubSynthesisAgent,
]:
    retrieval_agent = StubRetrievalAgent()
    analysis_agent = StubAnalysisAgent()
    synthesis_agent = StubSynthesisAgent()

    coordinator = MultiAgentCoordinator(
        retrieval_agent=retrieval_agent,
        analysis_agent=analysis_agent,
        synthesis_agent=synthesis_agent,
    )

    return (
        coordinator,
        retrieval_agent,
        analysis_agent,
        synthesis_agent,
    )


def test_coordinator_runs_complete_agent_pipeline() -> None:
    (
        coordinator,
        retrieval_agent,
        analysis_agent,
        synthesis_agent,
    ) = build_coordinator()

    result = coordinator.execute(make_task())

    assert len(result.evidence) == 1
    assert result.analysis.summary == ("AI agents require careful evaluation.")
    assert result.synthesis.answer == ("AI agents require careful evaluation.")

    assert retrieval_agent.tasks == [
        "Investigate AI agent reliability.",
    ]
    assert analysis_agent.received_evidence == result.evidence
    assert synthesis_agent.received_evidence == result.evidence
    assert synthesis_agent.received_analysis == result.analysis


def test_coordinator_preserves_agent_dependency_order() -> None:
    events: list[str] = []

    class OrderedRetrievalAgent(StubRetrievalAgent):
        def execute(self, task: ResearchTask) -> list[Evidence]:
            events.append("retrieval")
            return super().execute(task)

    class OrderedAnalysisAgent(StubAnalysisAgent):
        def execute(
            self,
            task: ResearchTask,
            evidence: list[Evidence],
        ) -> AnalysisResult:
            events.append("analysis")
            return super().execute(task, evidence)

    class OrderedSynthesisAgent(StubSynthesisAgent):
        def execute(
            self,
            task: ResearchTask,
            evidence: list[Evidence],
            analysis: AnalysisResult,
        ) -> SynthesisResult:
            events.append("synthesis")
            return super().execute(task, evidence, analysis)

    coordinator = MultiAgentCoordinator(
        retrieval_agent=OrderedRetrievalAgent(),
        analysis_agent=OrderedAnalysisAgent(),
        synthesis_agent=OrderedSynthesisAgent(),
    )

    coordinator.execute(make_task())

    assert events == [
        "retrieval",
        "analysis",
        "synthesis",
    ]


def test_coordinator_rejects_empty_retrieval() -> None:
    class EmptyRetrievalAgent:
        def execute(self, task: ResearchTask) -> list[Evidence]:
            return []

    coordinator = MultiAgentCoordinator(
        retrieval_agent=EmptyRetrievalAgent(),
        analysis_agent=StubAnalysisAgent(),
        synthesis_agent=StubSynthesisAgent(),
    )

    try:
        coordinator.execute(make_task())
    except ValueError as exc:
        assert str(exc) == "retrieval agent returned no evidence"
    else:
        raise AssertionError("Expected ValueError")
