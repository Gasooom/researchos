"""LLM provider factories for ResearchOS."""

from app.core.config import Settings
from app.infrastructure.llm.openai_client import OpenAILLMClient
from app.infrastructure.llm.provider import LLMProviderAdapter


def create_llm_provider(settings: Settings) -> LLMProviderAdapter:
    """Create the configured production LLM provider."""
    client = OpenAILLMClient(settings)

    return LLMProviderAdapter(
        client=client,
    )
