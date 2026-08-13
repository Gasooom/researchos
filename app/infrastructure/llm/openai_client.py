"""OpenAI-backed LLM client for ResearchOS."""

import json

from openai import OpenAI

from app.core.config import Settings


class OpenAILLMClient:
    """Generate structured JSON through the OpenAI API."""

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required to create an OpenAI client.")

        self.client = OpenAI(
            api_key=settings.openai_api_key,
        )
        self.model = settings.llm_model

    def generate(
        self,
        prompt: str,
    ) -> list[dict[str, object]]:
        """Generate one JSON object from the configured model."""
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )

        output_text = response.output_text.strip()

        if not output_text:
            raise ValueError("OpenAI returned an empty response.")

        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise ValueError("OpenAI returned invalid JSON.") from exc

        if not isinstance(parsed, dict):
            raise ValueError("OpenAI response must be a JSON object.")

        return [parsed]
