"""LLM-as-a-judge evaluation for ResearchOS."""

import json

from app.domain.evaluation.models import EvaluationMetric, EvaluationResult
from app.domain.research.models import ResearchResult


class LLMJudgeEvaluator:
    """Evaluate research quality using a configured LLM judge."""

    def __init__(self, provider) -> None:
        self.provider = provider

    def evaluate(self, result: ResearchResult) -> EvaluationResult:
        """Evaluate research quality using an LLM judge."""
        prompt = self._build_prompt(result)

        raw_output = self.provider.generate(prompt)

        return self._parse_output(raw_output)

    @staticmethod
    def _build_prompt(result: ResearchResult) -> str:
        """Build a constrained evaluation prompt."""
        claims = "\n".join(f"- {claim.statement}" for claim in result.claims)

        evidence = "\n\n".join(
            (
                f"Source: {item.source.title}\n"
                f"Publisher: {item.source.publisher}\n"
                f"URL: {item.source.url}\n"
                f"Relevance: {item.relevance:.2f}\n"
                f"Excerpt: {item.excerpt}"
            )
            for claim in result.claims
            for item in claim.evidence
        )

        return (
            "You are an evaluation judge for an evidence-grounded "
            "research system.\n\n"
            "Evaluate only the supplied research result.\n"
            "Do not use outside knowledge.\n"
            "Judge the result on:\n"
            "1. factual support by the provided evidence\n"
            "2. evidence groundedness\n"
            "3. completeness of the answer\n"
            "4. appropriate uncertainty handling\n\n"
            "Return exactly one JSON object with these fields:\n"
            '- "groundedness": number between 0 and 1\n'
            '- "completeness": number between 0 and 1\n'
            '- "uncertainty_handling": number between 0 and 1\n'
            '- "overall_score": number between 0 and 1\n'
            '- "reasoning": concise explanation\n\n'
            f"Research question:\n{result.question}\n\n"
            f"Claims:\n{claims}\n\n"
            f"Evidence:\n{evidence}"
        )

    @staticmethod
    def _parse_output(
        raw_output: list[dict[str, object]],
    ) -> EvaluationResult:
        """Parse judge output into the standard evaluation result."""
        if len(raw_output) != 1:
            raise ValueError("LLM judge provider must return exactly one result")

        parsed = raw_output[0]

        if "judgment" in parsed:
            raw_judgment = parsed["judgment"]

            if not isinstance(raw_judgment, str):
                raise ValueError("LLM judge 'judgment' field must be a JSON string")

            try:
                parsed = json.loads(raw_judgment)
            except json.JSONDecodeError as exc:
                raise ValueError("LLM judge provider returned invalid JSON") from exc

        if not isinstance(parsed, dict):
            raise ValueError("LLM judge provider returned invalid structured output")

        required_fields = {
            "groundedness",
            "completeness",
            "uncertainty_handling",
            "overall_score",
        }

        if not required_fields.issubset(parsed):
            raise ValueError(
                "LLM judge provider response must contain "
                "'judgment' or the direct evaluation fields"
            )

        reasoning = parsed.get("reasoning", "")

        if not isinstance(reasoning, str):
            raise ValueError("LLM judge reasoning must be a string")

        try:
            groundedness = float(parsed["groundedness"])
            completeness = float(parsed["completeness"])
            uncertainty_handling = float(parsed["uncertainty_handling"])
            overall_score = float(parsed["overall_score"])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "LLM judge provider returned invalid evaluation fields"
            ) from exc

        metrics = [
            EvaluationMetric(
                name="llm_groundedness",
                value=groundedness,
                description="LLM-judged evidence groundedness.",
            ),
            EvaluationMetric(
                name="llm_completeness",
                value=completeness,
                description="LLM-judged research completeness.",
            ),
            EvaluationMetric(
                name="llm_uncertainty_handling",
                value=uncertainty_handling,
                description="LLM-judged uncertainty handling.",
            ),
            EvaluationMetric(
                name="llm_judge_overall",
                value=overall_score,
                description=reasoning,
            ),
        ]

        return EvaluationResult(
            metrics=metrics,
            overall_score=overall_score,
        )
