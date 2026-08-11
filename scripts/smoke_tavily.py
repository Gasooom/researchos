"""Manual smoke test for the real Tavily integration."""

from app.core.config import Settings
from app.core.models.research import ResearchTask
from app.core.services.research_agent import ResearchAgent
from app.core.services.tavily_client import create_tavily_client
from app.core.services.tavily_search_provider import TavilySearchProvider


def main() -> None:
    """Run a real Tavily search through the ResearchOS stack."""
    settings = Settings()

    client = create_tavily_client(settings)
    provider = TavilySearchProvider(client)
    agent = ResearchAgent(provider)

    task = ResearchTask(
        objective="Investigate AI agent reliability.",
        task_type="reliability",
        max_sources=3,
    )

    evidence = agent.research(task)

    print(f"Evidence found: {len(evidence)}")

    for index, item in enumerate(evidence, start=1):
        print(f"{index}. {item.source.title}")
        print(f"   URL: {item.source.url}")
        print(f"   Publisher: {item.source.publisher}")
        print(f"   Relevance: {item.relevance}")
        print(f"   Excerpt: {item.excerpt[:150]}")
        print()


if __name__ == "__main__":
    main()
