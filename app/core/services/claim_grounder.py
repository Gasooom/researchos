"""Claim grounding services for ResearchOS."""

from app.core.models.research import Claim, Evidence


class ClaimGrounder:
    """Create claims that are explicitly grounded in evidence."""

    def ground(
        self,
        statement: str,
        evidence: list[Evidence],
    ) -> Claim:
        """Create a validated claim from supporting evidence."""
        if not statement.strip():
            raise ValueError("statement must not be empty")

        if not evidence:
            raise ValueError("evidence must not be empty")

        return Claim(
            statement=statement.strip(),
            evidence=evidence,
        )
