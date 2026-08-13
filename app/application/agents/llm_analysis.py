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

        raw_output = self.provider.generate(
            self._build_prompt(
                task=task,
                evidence=evidence,
            )
        )

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
            '- "key_points": a non-empty JSON array of findings\n'
            '- "confidence": a number between 0 and 1 reflecting how strongly '
            "the provided evidence supports the analysis\n\n"
            "Each key point may be either:\n"
            "- a string, or\n"
            '- an object containing "finding" or "statement", optionally with '
            '"type".\n\n'
            f"Research objective:\n{task.objective}\n\n"
            f"Provided evidence:\n{evidence_text}"
        )

    @staticmethod
    def _parse_output(
        raw_output: list[dict[str, object]],
    ) -> AnalysisResult:
        """Parse provider output into a validated AnalysisResult."""
        if len(raw_output) != 1:
            raise ValueError("LLM analysis provider must return exactly one result")

        parsed = raw_output[0]

        if "analysis" in parsed:
            raw_analysis = parsed["analysis"]

            if not isinstance(raw_analysis, str):
                raise ValueError("LLM analysis 'analysis' field must be a JSON string")

            try:
                parsed = json.loads(raw_analysis)
            except json.JSONDecodeError as exc:
                raise ValueError("LLM analysis provider returned invalid JSON") from exc

        if not isinstance(parsed, dict):
            raise ValueError("LLM analysis provider returned invalid structured output")

        if not {
            "summary",
            "key_points",
            "confidence",
        }.issubset(parsed):
            raise ValueError(
                "LLM analysis provider response must contain "
                "'analysis' or the direct analysis fields"
            )

        key_points = parsed["key_points"]

        if not isinstance(key_points, list):
            raise ValueError("LLM analysis key_points must be a list")

        normalized_key_points: list[str] = []

        for point in key_points:
            if isinstance(point, str):
                normalized_key_points.append(point)
                continue

            if isinstance(point, dict):
                finding = point.get("finding")

                if finding is None:
                    finding = point.get("statement")

                if not isinstance(finding, str) or not finding.strip():
                    raise ValueError(
                        "LLM analysis key point object must contain "
                        "a non-empty 'finding' or 'statement'"
                    )

                point_type = point.get("type")

                if isinstance(point_type, str) and point_type.strip():
                    normalized_key_points.append(
                        f"[{point_type.strip()}] {finding.strip()}"
                    )
                else:
                    normalized_key_points.append(finding.strip())
                continue

            raise ValueError("LLM analysis key points must contain strings or objects")

        normalized = {
            **parsed,
            "key_points": normalized_key_points,
        }

        return AnalysisResult.model_validate(normalized)
