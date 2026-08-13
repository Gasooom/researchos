"""Semantic quality evaluation for ResearchOS benchmarks."""

import re

from app.domain.evaluation.benchmark import BenchmarkEvaluationInput
from app.domain.evaluation.models import EvaluationMetric, EvaluationResult


class SemanticQualityEvaluator:
    """Evaluate benchmark-specific semantic research quality."""

    def evaluate(
        self,
        evaluation_input: BenchmarkEvaluationInput,
    ) -> EvaluationResult:
        """Compute deterministic semantic quality metrics."""
        case = evaluation_input.case
        result = evaluation_input.result
        multi_agent_results = evaluation_input.multi_agent_results

        if case.question.strip() != result.question.strip():
            raise ValueError("benchmark case question does not match research result")

        if not result.claims:
            raise ValueError("research result contains no claims")

        if not result.sources:
            raise ValueError("research result contains no sources")

        focus_coverage = self._focus_coverage(
            case=case,
            result=result,
            multi_agent_results=multi_agent_results,
        )

        claim_source_diversity = self._claim_source_diversity(result)

        evidence_breadth = self._evidence_breadth(result)

        synthesis_quality = self._synthesis_quality(multi_agent_results)

        metrics = [
            EvaluationMetric(
                name="focus_coverage",
                value=focus_coverage,
                description=(
                    "Fraction of expected benchmark focus areas represented "
                    "in the available research artifacts."
                ),
            ),
            EvaluationMetric(
                name="claim_source_diversity",
                value=claim_source_diversity,
                description=(
                    "Fraction of claims supported by distinct evidence sources."
                ),
            ),
            EvaluationMetric(
                name="evidence_breadth",
                value=evidence_breadth,
                description=("Normalized score based on distinct supporting sources."),
            ),
            EvaluationMetric(
                name="synthesis_quality",
                value=synthesis_quality,
                description=(
                    "Quality signal derived from analysis and synthesis "
                    "artifacts when available."
                ),
            ),
        ]

        overall_score = (
            focus_coverage
            + claim_source_diversity
            + evidence_breadth
            + synthesis_quality
        ) / 4

        return EvaluationResult(
            metrics=metrics,
            overall_score=overall_score,
        )

    @classmethod
    def _focus_coverage(
        cls,
        case,
        result,
        multi_agent_results,
    ) -> float:
        """Measure expected focus across available research text."""
        text_parts = [
            result.question,
            *(claim.statement for claim in result.claims),
        ]

        for agent_result in multi_agent_results:
            text_parts.extend(
                [
                    agent_result.analysis.summary,
                    *agent_result.analysis.key_points,
                    agent_result.synthesis.answer,
                    *agent_result.synthesis.supporting_points,
                ]
            )

        text_tokens = cls._token_set(" ".join(text_parts))

        if not case.expected_focus:
            return 1.0

        scores = [
            cls._focus_match_score(
                text_tokens=text_tokens,
                focus=focus,
            )
            for focus in case.expected_focus
        ]

        return sum(scores) / len(scores)

    @classmethod
    def _focus_match_score(
        cls,
        text_tokens: set[str],
        focus: str,
    ) -> float:
        """Return partial credit for overlapping focus tokens."""
        focus_tokens = cls._token_set(focus)

        if not focus_tokens:
            return 0.0

        overlap = len(text_tokens & focus_tokens)

        return overlap / len(focus_tokens)

    @staticmethod
    def _claim_source_diversity(result) -> float:
        """Measure how broadly claims are supported by sources."""
        claim_source_sets = [
            {str(evidence.source.url).rstrip("/") for evidence in claim.evidence}
            for claim in result.claims
        ]

        if not claim_source_sets:
            return 0.0

        claims_with_sources = sum(bool(source_set) for source_set in claim_source_sets)

        unique_primary_sources: set[str] = set()

        for source_set in claim_source_sets:
            if source_set:
                unique_primary_sources.add(sorted(source_set)[0])

        coverage = claims_with_sources / len(claim_source_sets)

        if len(claim_source_sets) == 1:
            source_spread = 1.0
        else:
            source_spread = min(
                len(unique_primary_sources) / len(claim_source_sets),
                1.0,
            )

        return (coverage + source_spread) / 2

    @staticmethod
    def _token_set(text: str) -> set[str]:
        """Tokenize text into normalized content words."""
        return {
            token
            for token in re.findall(
                r"\w+",
                text.lower(),
            )
            if len(token) > 2
        }

    @staticmethod
    def _evidence_breadth(result) -> float:
        """Compute a bounded score from distinct sources."""
        unique_sources = {
            str(evidence.source.url).rstrip("/")
            for claim in result.claims
            for evidence in claim.evidence
        }

        return min(
            len(unique_sources) / 3.0,
            1.0,
        )

    @staticmethod
    def _synthesis_quality(
        multi_agent_results,
    ) -> float:
        """Score multi-agent analysis and synthesis quality."""
        if not multi_agent_results:
            return 0.0

        scores: list[float] = []

        for agent_result in multi_agent_results:
            analysis = agent_result.analysis
            synthesis = agent_result.synthesis

            analysis_confidence = analysis.confidence
            synthesis_confidence = synthesis.confidence

            analysis_completeness = min(
                len(analysis.key_points) / 5.0,
                1.0,
            )

            synthesis_completeness = min(
                len(synthesis.supporting_points) / 5.0,
                1.0,
            )

            scores.append(
                (
                    analysis_confidence
                    + synthesis_confidence
                    + analysis_completeness
                    + synthesis_completeness
                )
                / 4
            )

        return sum(scores) / len(scores)
