"""Provider adapters for LLM-backed ResearchOS services."""

from typing import Protocol


class LLMClient(Protocol):
    """Protocol for providers that generate structured data."""

    def generate(
        self,
        prompt: str,
    ) -> list[dict[str, object]]:
        """Generate structured data from a prompt."""
        ...


class LLMProvider(Protocol):
    """Contract for providers capable of structured generation."""

    def generate(
        self,
        prompt: str,
    ) -> list[dict[str, object]]:
        """Generate structured data from a prompt."""
        ...


class LLMProviderAdapter:
    """Adapt a concrete LLM client to the ResearchOS provider contract."""

    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def generate(
        self,
        prompt: str,
    ) -> list[dict[str, object]]:
        """Generate structured data through the configured client."""
        return self.client.generate(prompt)
