import json

import pytest

from app.core.config import Settings
from app.infrastructure.llm.openai_client import OpenAILLMClient


def test_openai_client_requires_api_key() -> None:
    settings = Settings(
        OPENAI_API_KEY=None,
    )

    with pytest.raises(
        ValueError,
        match="OPENAI_API_KEY is required",
    ):
        OpenAILLMClient(settings)


def test_openai_client_parses_json_response(monkeypatch) -> None:
    settings = Settings(
        OPENAI_API_KEY="test-key",
        LLM_MODEL="test-model",
    )

    client = OpenAILLMClient(settings)

    class StubResponse:
        output_text = json.dumps(
            {
                "analysis": json.dumps(
                    {
                        "summary": "Test summary.",
                        "key_points": ["Test point."],
                        "confidence": 0.9,
                    }
                )
            }
        )

    class StubResponses:
        def create(self, **kwargs):
            assert kwargs["model"] == "test-model"
            assert kwargs["input"] == "test prompt"
            return StubResponse()

    client.client.responses = StubResponses()

    result = client.generate("test prompt")

    assert result == [
        {
            "analysis": json.dumps(
                {
                    "summary": "Test summary.",
                    "key_points": ["Test point."],
                    "confidence": 0.9,
                }
            )
        }
    ]


def test_openai_client_rejects_empty_response(monkeypatch) -> None:
    settings = Settings(
        OPENAI_API_KEY="test-key",
        LLM_MODEL="test-model",
    )

    client = OpenAILLMClient(settings)

    class StubResponse:
        output_text = ""

    class StubResponses:
        def create(self, **kwargs):
            return StubResponse()

    client.client.responses = StubResponses()

    with pytest.raises(
        ValueError,
        match="empty response",
    ):
        client.generate("test prompt")


def test_openai_client_rejects_non_object_json() -> None:
    settings = Settings(
        OPENAI_API_KEY="test-key",
        LLM_MODEL="test-model",
    )

    client = OpenAILLMClient(settings)

    class StubResponse:
        output_text = "[]"

    class StubResponses:
        def create(self, **kwargs):
            return StubResponse()

    client.client.responses = StubResponses()

    with pytest.raises(
        ValueError,
        match="JSON object",
    ):
        client.generate("test prompt")
