"""Lightweight conflict detection for ResearchOS."""

import re

from app.domain.research.models import Claim


class ClaimConflictDetector:
    """Detect obvious conflicts between evidence items."""

    _NEGATION_PHRASES = (
        "does not",
        "do not",
        "did not",
        "is not",
        "are not",
        "was not",
        "were not",
        "cannot",
        "can not",
        "will not",
        "should not",
        "never",
        "without",
        "not",
        "no",
    )

    def has_conflict(self, claim: Claim) -> bool:
        """Return whether evidence contains an obvious contradiction."""
        if len(claim.evidence) < 2:
            return False

        statements = [self._normalize(evidence.excerpt) for evidence in claim.evidence]

        for index, current in enumerate(statements):
            for other in statements[index + 1 :]:
                if self._pair_conflicts(current, other):
                    return True

        return False

    def _pair_conflicts(
        self,
        first: str,
        second: str,
    ) -> bool:
        """Detect shared content with opposite polarity."""
        first_content = self._content_tokens(first)
        second_content = self._content_tokens(second)

        if not first_content or not second_content:
            return False

        overlap = len(first_content & second_content) / len(
            first_content | second_content
        )

        if overlap < 0.5:
            return False

        return self._is_negative(first) != self._is_negative(second)

    def _is_negative(self, text: str) -> bool:
        """Return whether text contains an explicit negation phrase."""
        normalized = self._normalize(text)

        return any(phrase in normalized for phrase in self._NEGATION_PHRASES)

    def _content_tokens(self, text: str) -> set[str]:
        """Return normalized content tokens without negation phrases."""
        normalized = self._normalize(text)

        for phrase in self._NEGATION_PHRASES:
            normalized = normalized.replace(
                phrase,
                " ",
            )

        tokens = re.findall(
            r"\w+",
            normalized,
        )

        return {self._normalize_word(token) for token in tokens if len(token) > 2}

    @staticmethod
    def _normalize_word(token: str) -> str:
        """Normalize simple English word variants for comparison."""
        if token.endswith("ies") and len(token) > 4:
            return token[:-3] + "y"

        if token.endswith("es") and len(token) > 4:
            return token[:-2]

        if token.endswith("s") and len(token) > 3:
            return token[:-1]

        return token

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for deterministic comparison."""
        return " ".join(
            re.findall(
                r"\w+",
                text.lower(),
            )
        )
