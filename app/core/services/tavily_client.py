"""Tavily client creation for ResearchOS."""

from tavily import TavilyClient

from app.core.config import Settings


def create_tavily_client(settings: Settings) -> TavilyClient:
    """Create a Tavily client from application settings."""
    if not settings.tavily_api_key:
        raise ValueError("TAVILY_API_KEY is required to create a Tavily client.")

    return TavilyClient(api_key=settings.tavily_api_key)
