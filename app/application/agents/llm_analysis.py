"""LLM-backed analysis agent for ResearchOS."""

import json

from app.application.agents.roles import AgentRole
from app.domain.research.analysis import AnalysisResult
from app.domain.research.models import Evidence, ResearchTask


class LLMAnalysisAgent:
    """Analyze research evidence using a configured LLM provider."""

    def __init__(self, provider) -> None:
        self.provider = provider

    @property
    def role(self) -> AgentRole:
        """Return this agent's specialization."""
        return AgentRole.ANALYSIS

    def execute(
        self,
        task: ResearchTask,
        evidence: list[Evidence],
    ) -> AnalysisResult:
        """Generate and validate an evidence-grounded analysis."""
        if not evidence:
            raise ValueError("evidence must not be empty")

        prompt = self._build_prompt(
            task=task,
            evidence=evidence,
        )

        raw_output = self.provider.generate(prompt)

        return self._parse_output(raw_output)

    @staticmethod
    def _build_prompt(
        task: ResearchTask,
        evidence: list[Evidence],
    ) -> str:
        """Build a strict evidence-aware analysis prompt."""
        evidence_text = "\n\n".join(
            (
                f"[Evidence {index}]\n"
                f"Source title: {item.source.title}\n"
                f"Publisher: {item.source.publisher}\n"
                f"URL: {item.source.url}\n"
                f"Relevance: {item.relevance:.2f}\n"
                f"Excerpt: {item.excerpt}"
            )
            for index, item in enumerate(evidence, start=1)
        )

        return (
            "You are the analysis specialist in an evidence-grounded "
            "research system.\n\n"
            "Your job is to analyze ONLY the provided evidence.\n"
            "Do not add facts that are not supported by the evidence.\n"
            "Clearly distinguish direct evidence from inference.\n"
            "When the evidence is incomplete or conflicting, preserve that "
            "uncertainty instead of inventing certainty.\n"
            "Do not use outside knowledge.\n\n"
            "Return exactly one JSON object with these fields:\n"
            '- "summary": a concise evidence-grounded analytical summary\n'
            '- "key_points": a non-empty JSON array of evidence-grounded findings\n'
            '- "confidence": a number between 0 and 1 reflecting how strongly '
            "the provided evidence supports the analysis\n\n"
            f"Research objective:\n{task.objective}\n\n"
            f"Provided evidence:\n{evidence_text}"
        )

    @staticmethod
    def _parse_output(
        raw_output: list[dict[str, str]],
    ) -> AnalysisResult:
        """Parse provider output into a validated AnalysisResult."""
        if len(raw_output) != 1:
            raise ValueError("LLM analysis provider must return exactly one result")

        raw_analysis = raw_output[0].get("analysis")

        if raw_analysis is None:
            raise ValueError("LLM analysis provider response must contain 'analysis'")

        try:
            parsed = json.loads(raw_analysis)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM analysis provider returned invalid JSON") from exc

        return AnalysisResult.model_validate(parsed)
