"""Claim deduplication services for ResearchOS."""

import re
from difflib import SequenceMatcher

from app.domain.research.models import Claim, Evidence
from app.domain.research.review import ReviewStatus


class ClaimDeduplicator:
    """Merge claims that express substantially the same idea."""

    def __init__(
        self,
        similarity_threshold: float = 0.78,
        token_overlap_threshold: float = 0.78,
    ) -> None:
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError(
                "similarity_threshold must be between 0 and 1",
            )

        if not 0.0 <= token_overlap_threshold <= 1.0:
            raise ValueError(
                "token_overlap_threshold must be between 0 and 1",
            )

        self.similarity_threshold = similarity_threshold
        self.token_overlap_threshold = token_overlap_threshold

    def deduplicate(
        self,
        claims: list[Claim],
    ) -> list[Claim]:
        """Merge near-duplicate claims while preserving their evidence."""
        if not claims:
            return []

        deduplicated: list[Claim] = []

        for claim in claims:
            match_index = self._find_match(
                claim.statement,
                deduplicated,
            )

            if match_index is None:
                deduplicated.append(claim)
                continue

            existing = deduplicated[match_index]

            deduplicated[match_index] = Claim(
                statement=self._choose_statement(
                    existing.statement,
                    claim.statement,
                ),
                evidence=self._merge_evidence(
                    existing.evidence,
                    claim.evidence,
                ),
                review_status=self._merge_review_status(
                    existing.review_status,
                    claim.review_status,
                ),
            )

        return deduplicated

    def _find_match(
        self,
        statement: str,
        claims: list[Claim],
    ) -> int | None:
        """Find an existing claim that is sufficiently similar."""
        for index, existing in enumerate(claims):
            sequence_score, token_score = self._similarity_scores(
                statement,
                existing.statement,
            )

            if (
                sequence_score >= self.similarity_threshold
                or token_score >= self.token_overlap_threshold
            ):
                return index

        return None

    def _similarity_scores(
        self,
        left: str,
        right: str,
    ) -> tuple[float, float]:
        """Return sequence similarity and token overlap."""
        normalized_left = self._normalize(left)
        normalized_right = self._normalize(right)

        if normalized_left == normalized_right:
            return 1.0, 1.0

        sequence_score = SequenceMatcher(
            None,
            normalized_left,
            normalized_right,
        ).ratio()

        left_tokens = set(normalized_left.split())
        right_tokens = set(normalized_right.split())

        if not left_tokens or not right_tokens:
            return sequence_score, 0.0

        intersection = len(
            left_tokens & right_tokens,
        )

        smaller_set_size = min(
            len(left_tokens),
            len(right_tokens),
        )

        token_overlap = intersection / smaller_set_size if smaller_set_size else 0.0

        return sequence_score, token_overlap

    @staticmethod
    def _normalize(value: str) -> str:
        """Normalize text for deterministic comparison."""
        value = value.lower()

        value = re.sub(
            r"[^a-z0-9\s]",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    @staticmethod
    def _choose_statement(
        left: str,
        right: str,
    ) -> str:
        """Prefer the more informative statement."""
        if len(right) > len(left):
            return right

        return left

    @staticmethod
    def _merge_evidence(
        existing: list[Evidence],
        incoming: list[Evidence],
    ) -> list[Evidence]:
        """Merge unique evidence and rank by relevance."""
        merged: list[Evidence] = []
        seen: set[tuple[str, str]] = set()

        for evidence in [
            *existing,
            *incoming,
        ]:
            key = (
                str(evidence.source.url),
                evidence.excerpt.strip(),
            )

            if key in seen:
                continue

            seen.add(key)
            merged.append(evidence)

        return sorted(
            merged,
            key=lambda item: item.relevance,
            reverse=True,
        )

    @staticmethod
    def _merge_review_status(
        left: ReviewStatus,
        right: ReviewStatus,
    ) -> ReviewStatus:
        """Preserve the most restrictive review state."""
        priority = {
            ReviewStatus.NOT_REQUIRED: 0,
            ReviewStatus.PENDING: 1,
            ReviewStatus.APPROVED: 2,
            ReviewStatus.REJECTED: 3,
        }

        if priority[right] > priority[left]:
            return right

        return left
