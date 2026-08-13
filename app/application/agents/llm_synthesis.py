"""LLM-backed synthesis agent for ResearchOS."""

import json

from app.application.agents.roles import AgentRole
from app.domain.research.analysis import AnalysisResult
from app.domain.research.models import Evidence, ResearchTask
from app.domain.research.synthesis import SynthesisResult


class LLMSynthesisAgent:
    """Synthesize research analysis using a configured LLM provider."""

    def __init__(self, provider) -> None:
        self.provider = provider

    @property
    def role(self) -> AgentRole:
        """Return this agent's specialization."""
        return AgentRole.SYNTHESIS

    def execute(
        self,
        task: ResearchTask,
        evidence: list[Evidence],
        analysis: AnalysisResult,
    ) -> SynthesisResult:
        """Generate and validate an evidence-grounded synthesis."""
        if not evidence:
            raise ValueError("evidence must not be empty")

        if not analysis.key_points:
            raise ValueError("analysis must contain key points")

        raw_output = self.provider.generate(
            self._build_prompt(
                task=task,
                evidence=evidence,
                analysis=analysis,
            )
        )

        return self._parse_output(raw_output)

    @staticmethod
    def _build_prompt(
        task: ResearchTask,
        evidence: list[Evidence],
        analysis: AnalysisResult,
    ) -> str:
        """Build a strict evidence-aware synthesis prompt."""
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

        key_points = "\n".join(f"- {point}" for point in analysis.key_points)

        return (
            "You are the synthesis specialist in an evidence-grounded "
            "research system.\n\n"
            "Synthesize ONLY from the supplied evidence and analysis.\n"
            "Do not introduce unsupported facts or outside knowledge.\n"
            "Preserve uncertainty and important limitations from the analysis.\n"
            "Do not convert weak or incomplete evidence into certainty.\n"
            "The final answer must be traceable to the supplied material.\n\n"
            "Return exactly one JSON object with these fields:\n"
            '- "answer": a concise, evidence-grounded research answer\n'
            '- "supporting_points": a non-empty JSON array of findings\n'
            '- "confidence": a number between 0 and 1 reflecting support from '
            "the provided evidence and analysis\n\n"
            "Each supporting point may be either:\n"
            "- a string, or\n"
            '- an object containing "finding" or "statement", optionally with '
            '"type".\n\n'
            f"Research objective:\n{task.objective}\n\n"
            f"Analysis summary:\n{analysis.summary}\n\n"
            f"Analysis key findings:\n{key_points}\n\n"
            f"Provided evidence:\n{evidence_text}"
        )

    @staticmethod
    def _parse_output(
        raw_output: list[dict[str, object]],
    ) -> SynthesisResult:
        """Parse provider output into a validated SynthesisResult."""
        if len(raw_output) != 1:
            raise ValueError("LLM synthesis provider must return exactly one result")

        parsed = raw_output[0]

        if "synthesis" in parsed:
            raw_synthesis = parsed["synthesis"]

            if not isinstance(raw_synthesis, str):
                raise ValueError(
                    "LLM synthesis 'synthesis' field must be a JSON string"
                )

            try:
                parsed = json.loads(raw_synthesis)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "LLM synthesis provider returned invalid JSON"
                ) from exc

        if not isinstance(parsed, dict):
            raise ValueError(
                "LLM synthesis provider returned invalid structured output"
            )

        if not {
            "answer",
            "supporting_points",
            "confidence",
        }.issubset(parsed):
            raise ValueError(
                "LLM synthesis provider response must contain "
                "'synthesis' or the direct synthesis fields"
            )

        supporting_points = parsed["supporting_points"]

        if not isinstance(supporting_points, list):
            raise ValueError("LLM synthesis supporting_points must be a list")

        normalized_supporting_points: list[str] = []

        for point in supporting_points:
            if isinstance(point, str):
                normalized_supporting_points.append(point)
                continue

            if isinstance(point, dict):
                finding = point.get("finding")

                if finding is None:
                    finding = point.get("statement")

                if not isinstance(finding, str) or not finding.strip():
                    raise ValueError(
                        "LLM synthesis supporting point object must contain "
                        "a non-empty 'finding' or 'statement'"
                    )

                point_type = point.get("type")

                if isinstance(point_type, str) and point_type.strip():
                    normalized_supporting_points.append(
                        f"[{point_type.strip()}] {finding.strip()}"
                    )
                else:
                    normalized_supporting_points.append(finding.strip())
                continue

            raise ValueError(
                "LLM synthesis supporting points must contain strings or objects"
            )

        normalized = {
            **parsed,
            "supporting_points": normalized_supporting_points,
        }

        return SynthesisResult.model_validate(normalized)
