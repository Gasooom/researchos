"""Provider adapters for LLM-backed ResearchOS services."""

from typing import Protocol


class LLMClient(Protocol):
    """Protocol for provider clients that generate structured task data."""

    def generate(self, prompt: str) -> list[dict[str, str]]:
        """Generate structured task data from a prompt."""
        ...


class LLMProviderAdapter:
    """Adapt a concrete LLM client to the ResearchOS provider contract."""

    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def generate(self, prompt: str) -> list[dict[str, str]]:
        """Generate structured planning data through the configured client."""
        return self.client.generate(prompt)
