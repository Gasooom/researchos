from app.infrastructure.llm.provider import LLMProviderAdapter


class FakeClient:
    """Deterministic fake client for provider adapter tests."""

    def generate(self, prompt: str) -> list[dict[str, str]]:
        return [
            {
                "objective": "Research AI agent reliability.",
                "task_type": "research",
            },
            {
                "objective": "Evaluate reliability measurement methods.",
                "task_type": "evaluation",
            },
        ]


def test_provider_adapter_generates_structured_tasks() -> None:
    adapter = LLMProviderAdapter(client=FakeClient())

    tasks = adapter.generate("Create research tasks about AI agent reliability.")

    assert tasks == [
        {
            "objective": "Research AI agent reliability.",
            "task_type": "research",
        },
        {
            "objective": "Evaluate reliability measurement methods.",
            "task_type": "evaluation",
        },
    ]


def test_provider_adapter_passes_prompt_to_client() -> None:
    class RecordingClient:
        def __init__(self) -> None:
            self.received_prompt = None

        def generate(self, prompt: str) -> list[dict[str, str]]:
            self.received_prompt = prompt
            return [
                {
                    "objective": "Research reliability.",
                    "task_type": "research",
                }
            ]

    client = RecordingClient()
    adapter = LLMProviderAdapter(client=client)

    prompt = "Research AI agent reliability."
    adapter.generate(prompt)

    assert client.received_prompt == prompt
