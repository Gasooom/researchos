"""Workspace API models for ResearchOS."""

from pydantic import BaseModel

from app.domain.evaluation.models import EvaluationResult
from app.domain.research.models import ResearchResult
from app.domain.research.multi_agent import MultiAgentResearchResult
from app.domain.runs.models import ResearchRunOutcome
from app.domain.runs.observability import RunObservation


class WorkspaceResponse(BaseModel):
    """Complete workspace payload for the ResearchOS frontend."""

    result: ResearchResult
    execution: ResearchRunOutcome
    agents: list[MultiAgentResearchResult]
    evaluation: EvaluationResult
    observation: RunObservation | None = None
